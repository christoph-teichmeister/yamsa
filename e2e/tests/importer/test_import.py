import re
from decimal import Decimal

import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import BASE_CATEGORY_SLUGS, Category, ParentTransaction
from e2e.conftest import _login
from e2e.pages.import_page import ImportPage
from e2e.pages.side_menu_page import SideMenuPage

ME = "Ich Selbst"
FLATMATE = "Anna Beispiel"

# Anna owes 20.00 for the groceries, is owed 12.00 for the cinema and has already sent 5.00, which
# leaves 3.00 open. The unreadable cost and the closing balance line are both skipped.
EXPORT = f"""Datum,Beschreibung,Kategorie,Kosten,Währung,{ME},{FLATMATE}
2026-01-10,Wocheneinkauf,Lebensmittel,40.00,EUR,20.00,-20.00
2026-01-12,Kinokarten,Kino,24.00,EUR,-12.00,12.00
2026-01-15,Ausgleich,Zahlung,5.00,EUR,-5.00,5.00
2026-01-20,Kaputte Zeile,Allgemein,abc,EUR,1.00,-1.00
2026-01-31,Gesamtbilanz, , ,EUR,3.00,-3.00
""".encode()


@pytest.fixture
def catalog(transactional_db: None):
    # A transactional database flushes what the migrations seeded, and the preview offers exactly
    # the base categories that exist.
    for order_index, slug in enumerate(BASE_CATEGORY_SLUGS):
        Category.objects.get_or_create(
            slug=slug, defaults={"name": slug.replace("-", " ").title(), "emoji": "🏷️", "order_index": order_index}
        )
    return CurrencyFactory(code="EUR", sign="€")


@pytest.fixture
def import_page(page: Page, base_url: str, profile_user: User, user_password: str, catalog: None) -> ImportPage:
    _login(page, base_url, profile_user.email, user_password)
    upload_page = ImportPage(page, base_url, reverse("importer:upload"))
    upload_page.navigate()
    return upload_page


@pytest.fixture
def previewed_import(import_page: ImportPage) -> ImportPage:
    import_page.upload(name="splitwise.csv", content=EXPORT)
    import_page.expect_preview()
    return import_page


def _imported_room(name: str) -> Room:
    return Room.objects.get(name=name)


def _open_debts(room: Room) -> set[tuple[str, str, Decimal]]:
    return {
        (debt.debitor.name, debt.creditor.name, debt.value)
        for debt in Debt.objects.filter(room=room, settled=False).select_related("debitor", "creditor")
    }


@pytest.mark.e2e
class TestImport:
    def test_the_side_menu_leads_to_the_upload(
        self, page: Page, base_url: str, profile_user: User, user_password: str, catalog: None
    ):
        _login(page, base_url, profile_user.email, user_password)
        side_menu = SideMenuPage(page, base_url)
        side_menu.open_menu()

        page.locator("#side-menu-panel").get_by_role("button", name="Import").click()

        page.wait_for_url(lambda url: url.endswith(reverse("importer:upload")))
        expect(page.get_by_role("heading", name="Import transactions")).to_be_visible()

    def test_a_file_that_is_no_export_is_rejected_on_the_upload(self, import_page: ImportPage, page: Page):
        import_page.upload(name="notes.csv", content=b"just,some\nrandom,text\n")

        import_page.expect_upload_error("No person columns found.")
        expect(page).to_have_url(re.compile(rf"{re.escape(reverse('importer:upload'))}$"))
        assert not Room.objects.exists()

    def test_the_preview_sums_up_what_the_file_holds(self, previewed_import: ImportPage):
        expect(previewed_import.summary_value("Transactions")).to_have_text("2")
        expect(previewed_import.summary_value("Settlements")).to_have_text("1")
        expect(previewed_import.summary_value("Skipped rows")).to_have_text("2")
        expect(previewed_import.summary_value("Total EUR")).to_have_text("64.00")
        expect(previewed_import.page.get_by_text("Unreadable cost 'abc'")).to_be_visible()

    def test_the_preview_proposes_a_new_guest_and_a_matching_category(self, previewed_import: ImportPage):
        expect(previewed_import.person_assignment(FLATMATE)).to_have_value("guest")
        expect(previewed_import.category_assignment("Lebensmittel")).to_have_value("groceries")

    def test_confirming_creates_a_room_with_transactions_settlement_and_debt(
        self, previewed_import: ImportPage, page: Page, profile_user: User
    ):
        previewed_import.assign_person(ME, "me")
        previewed_import.create_category("Kino", name="Kino", emoji="🎬")
        previewed_import.set_room_name("WG Splitwise")
        previewed_import.confirm()

        room = _imported_room("WG Splitwise")
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        previewed_import.expect_toast("2 transactions imported, 1 settlements, 2 rows skipped")

        assert set(room.users.values_list("name", flat=True)) == {profile_user.name, FLATMATE}
        guest = room.users.get(name=FLATMATE)
        assert guest.is_guest
        transactions = {
            transaction.description: (transaction.paid_by.name, transaction.category.name)
            for transaction in ParentTransaction.objects.filter(room=room).select_related("paid_by", "category")
        }
        assert transactions == {
            "Wocheneinkauf": (profile_user.name, "Groceries"),
            "Kinokarten": (FLATMATE, "Kino"),
        }
        assert Debt.objects.filter(room=room, settled=True, debitor=guest, value=Decimal("5.00")).exists()
        assert _open_debts(room) == {(FLATMATE, profile_user.name, Decimal("3.00"))}

    def test_the_share_hint_greets_the_new_room_once(self, previewed_import: ImportPage, page: Page):
        previewed_import.assign_person(ME, "me")
        previewed_import.set_room_name("WG Splitwise")
        previewed_import.confirm()

        hint = page.get_by_role("status").filter(has_text="Share this room with the others")
        expect(hint).to_be_visible()
        expect(hint.get_by_role("button", name="Copy share link")).to_be_visible()

        page.reload()
        expect(hint).to_have_count(0)

    def test_someone_the_user_already_shares_a_room_with_is_reused(
        self, page: Page, base_url: str, profile_user: User, user_password: str, catalog: None
    ):
        anna = UserFactory(name=FLATMATE)
        RoomFactory(created_by=profile_user).users.add(profile_user, anna)
        _login(page, base_url, profile_user.email, user_password)
        import_page = ImportPage(page, base_url, reverse("importer:upload"))
        import_page.navigate()
        import_page.upload(name="splitwise.csv", content=EXPORT)

        expect(import_page.person_assignment(FLATMATE)).to_have_value(f"user-{anna.pk}")
        import_page.assign_person(ME, "me")
        import_page.set_room_name("WG Splitwise")
        import_page.confirm()

        room = _imported_room("WG Splitwise")
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        assert set(room.users.all()) == {profile_user, anna}
        assert _open_debts(room) == {(FLATMATE, profile_user.name, Decimal("3.00"))}

    def test_an_import_without_the_user_among_the_people_is_refused(self, previewed_import: ImportPage):
        previewed_import.confirm()

        previewed_import.expect_toast("Mark exactly one column as 'That is me'.")
        previewed_import.expect_preview()
        assert not Room.objects.exists()

    def test_a_new_category_without_a_single_emoji_is_refused(self, previewed_import: ImportPage):
        previewed_import.assign_person(ME, "me")
        previewed_import.create_category("Kino", name="Kino", emoji="no emoji")
        previewed_import.confirm()

        previewed_import.expect_preview()
        expect(previewed_import.category_assignment("Kino")).to_have_value("new")
        assert not Room.objects.exists()
