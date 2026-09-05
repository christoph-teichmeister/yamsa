from django.urls import reverse

from apps.importer.tests.factories import build_upload

MIXED_CURRENCY_ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Hotel,Allgemein,80.00,THB,40.00,-40.00",
]


class TestImportCurrencyWarning:
    """
    Codes without a Currency row are booked in the room currency, which merges foreign amounts
    into one balance. The preview has to say so before the user confirms.
    """

    def test_unknown_codes_are_listed_in_the_preview(self, db, authenticated_client, currency):
        redirect = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(MIXED_CURRENCY_ROWS)},
        )
        token = redirect.url.split("token=")[1]

        response = authenticated_client.get(f"{reverse('importer:preview')}?token={token}")

        assert response.context["unknown_currency_codes"] == ["THB"]
        assert "THB" in response.content.decode()

    def test_a_fully_known_file_shows_no_warning(self, db, authenticated_client, currency):
        redirect = authenticated_client.post(
            reverse("importer:upload"),
            data={"source": "splitwise-csv", "file": build_upload(MIXED_CURRENCY_ROWS[:1])},
        )
        token = redirect.url.split("token=")[1]

        response = authenticated_client.get(f"{reverse('importer:preview')}?token={token}")

        assert response.context["unknown_currency_codes"] == []
