from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.importer.constants import SESSION_KEY_PREFIX
from apps.importer.tests.factories import build_upload

ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
    "2026-09-05,Gesamtbilanz,,,EUR,47.77,-47.77",
]


def _stored_payload(session):
    """The parsed file lives under a per-upload token, so tests cannot address it by a fixed key."""
    for key, value in session.items():
        if key.startswith(f"{SESSION_KEY_PREFIX}:"):
            return value
    return None


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
        assert response.url.startswith(reverse("importer:preview"))
        payload = _stored_payload(authenticated_client.session)
        assert len(payload["transactions"]) == 2

    def test_non_csv_file_is_rejected(self, db, authenticated_client):
        upload = SimpleUploadedFile("export.txt", b"whatever", content_type="text/plain")

        response = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload}
        )

        assert response.status_code == 200
        assert _stored_payload(authenticated_client.session) is None

    def test_empty_file_is_rejected(self, db, authenticated_client):
        upload = SimpleUploadedFile("export.csv", b"", content_type="text/csv")

        response = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": upload}
        )

        assert response.status_code == 200
        assert _stored_payload(authenticated_client.session) is None

    def test_file_without_importable_rows_is_rejected(self, db, authenticated_client):
        response = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(["2026-09-05,Gesamtbilanz,,,EUR,1.00,-1.00"])},
        )

        assert response.status_code == 200
        assert _stored_payload(authenticated_client.session) is None
