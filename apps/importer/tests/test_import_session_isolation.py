from django.urls import reverse

from apps.importer.session import read_parsed_import, store_parsed_import
from apps.importer.tests.factories import build_upload

ROWS_A = ["2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20"]
HEADER_B = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Ben"
ROWS_B = ["2024-01-01,Kino,Kino,10.00,EUR,5.00,-5.00"]


class TestImportSessionIsolation:
    """A second upload tab must not overwrite the first tab's parsed file."""

    def test_two_uploads_are_stored_side_by_side(self, db, authenticated_client):
        first = authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": build_upload(ROWS_A)}
        )
        second = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(ROWS_B, header=HEADER_B)},
        )

        token_a = first.url.split("token=")[1]
        token_b = second.url.split("token=")[1]
        session = authenticated_client.session

        assert token_a != token_b
        assert read_parsed_import(session, token_a)["people"] == ["Kilian Karaus", "Elisabeth"]
        assert read_parsed_import(session, token_b)["people"] == ["Anna", "Ben"]

    def test_preview_renders_the_file_its_token_names(self, db, authenticated_client):
        authenticated_client.post(
            reverse("importer:upload"), data={"source": "splitwise-csv", "file": build_upload(ROWS_A)}
        )
        second = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(ROWS_B, header=HEADER_B)},
        )
        token_b = second.url.split("token=")[1]

        response = authenticated_client.get(f"{reverse('importer:preview')}?token={token_b}")

        assert response.context["parsed"].people == ("Anna", "Ben")

    def test_unknown_token_redirects_to_upload(self, db, authenticated_client):
        response = authenticated_client.get(f"{reverse('importer:preview')}?token=does-not-exist")

        assert response.status_code == 302
        assert response.url == reverse("importer:upload")

    def test_a_consumed_token_cannot_be_replayed(self, db, authenticated_client):
        session = authenticated_client.session
        token = store_parsed_import(session, {"people": []})
        session.save()

        from apps.importer.session import pop_parsed_import

        assert pop_parsed_import(authenticated_client.session, token) is not None
