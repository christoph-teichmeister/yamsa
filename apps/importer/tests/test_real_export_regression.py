from decimal import Decimal
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.importer.session import read_parsed_import
from apps.room.models import Room
from apps.transaction.models import ParentTransaction, RoomCategory

FIXTURE = Path(__file__).parent / "fixtures" / "splitwise_export_excerpt.csv"


@pytest.fixture
def currency(db):
    return Currency.objects.create(name="Euro", sign="€", code="EUR")


class TestRealSplitwiseExport:
    """Runs an excerpt of a genuine Splitwise export through the whole flow."""

    def _import(self, client, currency):
        upload = SimpleUploadedFile("Splitwise_expenses.csv", FIXTURE.read_bytes(), content_type="text/csv")
        redirect = client.post(reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload})
        token = redirect.url.split("token=")[1]

        response = client.get(f"{reverse('importer:preview')}?token={token}")
        form = response.context["form"]

        payload = {
            "token": token,
            "room_name": "Kilian & Elisabeth",
            "room_description": "Import aus Splitwise",
            "preferred_currency": str(currency.pk),
            "person_0": "me",
            "person_0_name": "Kilian Karaus",
            "person_1": "guest",
            "person_1_name": "Elisabeth",
        }
        for index, category in enumerate(form.parsed.categories):
            payload[f"category_{index}"] = category.suggested_slug
            payload[f"category_{index}_name"] = category.label
            payload[f"category_{index}_emoji"] = category.suggested_emoji

        return client.post(reverse("importer:preview"), data=payload)

    def test_import_writes_every_row_of_the_export(self, db, authenticated_client, currency):
        self._import(authenticated_client, currency)

        room = Room.objects.get()
        assert ParentTransaction.objects.filter(room=room).count() == 15

    def test_open_debt_matches_the_gesamtbilanz_line(self, db, authenticated_client, user, currency):
        # The fixture's summary row says Kilian is 43.75 down, so he owes Elisabeth exactly that.
        self._import(authenticated_client, currency)

        room = Room.objects.get()
        debt = Debt.objects.get(room=room, settled=False)
        assert debt.debitor == user
        assert debt.value == Decimal("43.75")

    def test_balance_summary_row_is_the_only_skipped_row(self, db, authenticated_client, currency):
        upload = SimpleUploadedFile("Splitwise_expenses.csv", FIXTURE.read_bytes(), content_type="text/csv")
        redirect = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload}
        )
        token = redirect.url.split("token=")[1]

        skipped = read_parsed_import(authenticated_client.session, token)["skipped_rows"]
        assert len(skipped) == 1
        assert "Gesamtbilanz" in skipped[0]["excerpt"]

    def test_every_transaction_lands_in_a_room_category(self, db, authenticated_client, currency):
        self._import(authenticated_client, currency)

        room = Room.objects.get()
        room_category_ids = set(RoomCategory.objects.filter(room=room).values_list("category_id", flat=True))
        transaction_category_ids = set(
            ParentTransaction.objects.filter(room=room).values_list("category_id", flat=True)
        )
        assert transaction_category_ids <= room_category_ids
