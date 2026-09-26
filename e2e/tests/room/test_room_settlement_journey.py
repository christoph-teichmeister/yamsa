import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.models import DEFAULT_CATEGORY_SLUG, Category
from e2e.conftest import _login
from e2e.pages.dashboard_page import DashboardPage
from e2e.pages.debt_list_page import DebtListPage
from e2e.pages.room_create_page import RoomCreatePage
from e2e.pages.room_detail_page import RoomDetailPage
from e2e.pages.room_people_page import RoomPeoplePage
from e2e.pages.room_share_page import RoomSharePage
from e2e.pages.transaction_create_page import TransactionCreatePage

GUEST_NAME = "Alex aus der Küche"


@pytest.fixture
def catalog(transactional_db):
    # The transactional database flushes what the migrations seeded. A room created through the
    # UI links the base categories on first use, so they have to exist before it does.
    CurrencyFactory(code="EUR", sign="€")
    for order_index, (slug, name, emoji) in enumerate(
        ((DEFAULT_CATEGORY_SLUG, "Misc", "📦"), ("groceries", "Groceries", "🛒"))
    ):
        Category.objects.get_or_create(slug=slug, defaults={"name": name, "emoji": emoji, "order_index": order_index})


@pytest.mark.e2e
class TestRoomSettlementJourney:
    """One room from creation to closing, through the pages a real group would use.

    The single steps have their own, narrower tests; this one proves they hand over to each
    other - above all that an expense entered in the form becomes a debt the guest can settle.
    """

    def test_a_room_is_created_shared_settled_and_closed(self, catalog, profile_user, page, base_url, new_context):
        _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

        create_page = RoomCreatePage(page, base_url, reverse("room:create"))
        create_page.navigate()
        create_page.fill(name="Hütte am See", description="Wanderwoche")
        create_page.submit()
        page.wait_for_url(lambda url: url.endswith("/detail"))
        room = Room.objects.get(name="Hütte am See")

        people_page = RoomPeoplePage(page, base_url, reverse("account:list", kwargs={"room_slug": room.slug}))
        people_page.navigate()
        people_page.add_guest(GUEST_NAME)
        people_page.expect_member(GUEST_NAME)
        share_url = people_page.share_url()

        transaction_page = TransactionCreatePage(
            page, base_url, reverse("transaction:create", kwargs={"room_slug": room.slug})
        )
        transaction_page.navigate()
        transaction_page.fill_required_fields(description="Wocheneinkauf", amount="30.00")
        transaction_page.choose_category("groceries")
        transaction_page.submit()
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))

        # Split evenly between the two of them, so the guest owes the owner half.
        debt = Debt.objects.get(room=room, settled=False)
        assert debt.creditor == profile_user
        assert debt.debitor.name == GUEST_NAME

        debt_list_url = reverse("debt:list", kwargs={"room_slug": room.slug})
        owner_debt_list = DebtListPage(page, base_url, debt_list_url)
        owner_debt_list.navigate()
        owner_debt_list.expect_row(debt.id, text=f"{GUEST_NAME} owes you", amount="15.00")
        owner_debt_list.expect_open_for_creditor(debt.id)

        guest_page = new_context().new_page()
        share_page = RoomSharePage(guest_page, share_url)
        share_page.navigate()
        share_page.claim_guest_seat(GUEST_NAME)
        guest_page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))

        guest_debt_list = DebtListPage(guest_page, base_url, debt_list_url)
        guest_debt_list.navigate()
        guest_debt_list.expect_row(debt.id, text=f"You owe {profile_user.name}", amount="15.00")
        guest_debt_list.open_settle_confirmation(debt.id)
        guest_debt_list.confirm_settlement()
        guest_debt_list.expect_settled(debt.id)

        dashboard_page = DashboardPage(page, base_url, reverse("core:welcome"))
        dashboard_page.navigate()
        dashboard_page.expect_settled(
            reverse(Room.dashboard_viewname_for(room.status), kwargs={"room_slug": room.slug})
        )

        # Nothing is owed any more, so closing takes the plain confirmation, not the force-close.
        detail_page = RoomDetailPage(page, base_url, reverse("room:detail", kwargs={"room_slug": room.slug}))
        detail_page.navigate()
        detail_page.close_room()
        detail_page.expect_status("Closed")
        expect(page.locator("#force-close-dialog")).not_to_be_visible()
