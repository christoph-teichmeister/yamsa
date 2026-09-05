import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.currency.models import Currency
from apps.importer.constants import SESSION_KEY
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_csv, build_upload

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


class TestImportUploadView:
    def test_login_is_required(self, db, client):
        response = client.get(reverse("importer:upload"))

        assert response.status_code == 302

    def test_page_renders_for_a_logged_in_user(self, db, authenticated_client):
        response = authenticated_client.get(reverse("importer:upload"))

        assert response.status_code == 200

    def test_valid_upload_stores_the_parsed_file_in_the_session(self, db, authenticated_client):
        response = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(ROWS)},
        )

        assert response.status_code == 302
        assert response.url == reverse("importer:preview")
        assert len(authenticated_client.session[SESSION_KEY]["transactions"]) == 2

    def test_non_csv_file_is_rejected(self, db, authenticated_client):
        upload = SimpleUploadedFile("export.txt", b"whatever", content_type="text/plain")

        response = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload}
        )

        assert response.status_code == 200
        assert SESSION_KEY not in authenticated_client.session

    def test_empty_file_is_rejected(self, db, authenticated_client):
        upload = SimpleUploadedFile("export.csv", b"", content_type="text/csv")

        response = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload}
        )

        assert response.status_code == 200
        assert SESSION_KEY not in authenticated_client.session

    def test_file_without_importable_rows_is_rejected(self, db, authenticated_client):
        response = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(["2026-09-05,Gesamtbilanz,,,EUR,1.00,-1.00"])},
        )

        assert response.status_code == 200
        assert SESSION_KEY not in authenticated_client.session
