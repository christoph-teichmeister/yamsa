import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.account.tests.factories import GuestUserFactory
from apps.currency.models import Currency
from apps.importer.constants import SESSION_KEY
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_csv
from apps.room.models import Room
from apps.transaction.models import ParentTransaction

ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
    "2026-09-05,Gesamtbilanz,,,EUR,47.77,-47.77",
]


@pytest.fixture
def currency(db):
    return Currency.objects.create(name="Euro", sign="€", code="EUR")


@pytest.fixture
def preview_session(authenticated_client):
    parsed = SplitwiseCsvParser().parse(SimpleUploadedFile("e.csv", build_csv(ROWS).encode("utf-8")))
    session = authenticated_client.session
    session[SESSION_KEY] = parsed.as_payload()
    session.save()
    return parsed


def build_preview_payload(parsed, currency, **overrides):
    payload = {
        "room_name": "Kilian & Elisabeth",
        "room_description": "Import aus Splitwise",
        "preferred_currency": str(currency.pk),
        "person_0": "me",
        "person_0_name": "Kilian Karaus",
        "person_1": "guest",
        "person_1_name": "Elisabeth",
    }
    for index, category in enumerate(parsed.categories):
        payload[f"category_{index}"] = category.suggested_slug
        payload[f"category_{index}_name"] = category.label
        payload[f"category_{index}_emoji"] = category.suggested_emoji
    payload.update(overrides)
    return payload


class TestImportPreviewView:
    def test_login_is_required(self, db, client):
        response = client.get(reverse("importer:preview"))

        assert response.status_code == 302

    def test_redirects_to_upload_without_a_parsed_file(self, db, authenticated_client):
        response = authenticated_client.get(reverse("importer:preview"))

        assert response.status_code == 302
        assert response.url == reverse("importer:upload")

    def test_renders_the_person_and_category_rows(self, db, authenticated_client, preview_session, currency):
        response = authenticated_client.get(reverse("importer:preview"))

        assert response.status_code == 200
        assert "Kilian Karaus" in response.content.decode()
        assert "Elisabeth" in response.content.decode()

    def test_existing_person_is_preselected(self, db, authenticated_client, preview_session, currency, room):
        # A guest the importer already shares a room with must not be recreated by the import.
        existing = GuestUserFactory(name="Elisabeth")
        room.users.add(existing)

        response = authenticated_client.get(reverse("importer:preview"))
        form = response.context["form"]

        assert form["person_1"].initial == f"user-{existing.pk}"

    def test_unknown_person_defaults_to_a_new_guest(self, db, authenticated_client, preview_session, currency):
        response = authenticated_client.get(reverse("importer:preview"))
        form = response.context["form"]

        assert form["person_1"].initial == "guest"

    def test_import_creates_a_room_and_redirects(self, db, authenticated_client, preview_session, currency):
        response = authenticated_client.post(
            reverse("importer:preview"), data=build_preview_payload(preview_session, currency)
        )

        room = Room.objects.get()
        assert response.status_code == 302
        assert response.url == reverse("transaction:list", kwargs={"room_slug": room.slug})
        assert ParentTransaction.objects.filter(room=room).count() == 2

    def test_session_is_cleared_after_the_import(self, db, authenticated_client, preview_session, currency):
        authenticated_client.post(reverse("importer:preview"), data=build_preview_payload(preview_session, currency))

        assert SESSION_KEY not in authenticated_client.session

    def test_missing_self_assignment_is_rejected(self, db, authenticated_client, preview_session, currency):
        payload = build_preview_payload(preview_session, currency, person_0="guest")

        response = authenticated_client.post(reverse("importer:preview"), data=payload)

        assert response.status_code == 200
        assert Room.objects.count() == 0

    def test_two_self_assignments_are_rejected(self, db, authenticated_client, preview_session, currency):
        payload = build_preview_payload(preview_session, currency, person_1="me")

        response = authenticated_client.post(reverse("importer:preview"), data=payload)

        assert response.status_code == 200
        assert Room.objects.count() == 0

    def test_same_person_on_two_columns_is_rejected(self, db, authenticated_client, preview_session, currency, room):
        friend = GuestUserFactory(name="Elisabeth")
        room.users.add(friend)
        payload = build_preview_payload(
            preview_session, currency, person_0=f"user-{friend.pk}", person_1=f"user-{friend.pk}"
        )

        response = authenticated_client.post(reverse("importer:preview"), data=payload)

        assert response.status_code == 200
        assert not Room.objects.filter(name="Kilian & Elisabeth").exists()

    def test_new_category_without_a_valid_emoji_is_rejected(self, db, authenticated_client, preview_session, currency):
        payload = build_preview_payload(preview_session, currency)
        payload["category_0"] = "new"
        payload["category_0_name"] = "Möbel"
        payload["category_0_emoji"] = "nope"

        response = authenticated_client.post(reverse("importer:preview"), data=payload)

        assert response.status_code == 200
        assert Room.objects.count() == 0

    def test_share_hint_is_shown_once_after_the_import(self, db, authenticated_client, preview_session, currency):
        authenticated_client.post(reverse("importer:preview"), data=build_preview_payload(preview_session, currency))
        room = Room.objects.get()
        list_url = reverse("transaction:list", kwargs={"room_slug": room.slug})

        first = authenticated_client.get(list_url)
        second = authenticated_client.get(list_url)

        assert first.context["show_import_share_hint"] is True
        assert second.context["show_import_share_hint"] is False
