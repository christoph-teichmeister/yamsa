from unittest import mock

from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.currency.models import Currency
from apps.importer.models import ConsumedImportToken
from apps.importer.services.import_service import ImportService
from apps.importer.tests.factories import build_upload
from apps.room.models import Room

ROWS = ["2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20"]


class TestImportConfirmLock:
    """Two confirm POSTs that both read the session before either wrote must still create one room.

    A real thread race cannot run against the test database (SQLite serialises writers and the test
    transaction is one connection), so the loser is simulated by a claimed token row plus a session
    that still holds the payload, which is exactly what the second request sees.
    """

    def _token(self, client: Client) -> str:
        redirect = client.post(reverse("importer:upload"), data={"source": "splitwise-csv", "file": build_upload(ROWS)})
        return redirect.url.split("token=")[1]

    def _confirm(self, client: Client, token: str, currency: Currency) -> HttpResponse:
        form = client.get(f"{reverse('importer:preview')}?token={token}").context["form"]
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
        return client.post(reverse("importer:preview"), data=payload)

    def test_a_confirm_that_lost_the_race_creates_no_room(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)
        ConsumedImportToken.objects.create(token=token)

        response = self._confirm(authenticated_client, token, currency)

        assert response.status_code == 302
        assert response.url == reverse("importer:upload")
        assert not Room.objects.filter(name="Kilian & Elisabeth").exists()

    def test_a_successful_confirm_claims_the_token(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)

        self._confirm(authenticated_client, token, currency)

        assert ConsumedImportToken.objects.filter(token=token).exists()
        assert Room.objects.filter(name="Kilian & Elisabeth").count() == 1

    def test_a_failed_import_releases_the_token_so_a_retry_works(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)
        authenticated_client.raise_request_exception = False

        with mock.patch.object(ImportService, "process", side_effect=RuntimeError("boom")):
            self._confirm(authenticated_client, token, currency)
        assert not ConsumedImportToken.objects.filter(token=token).exists()

        retry = self._confirm(authenticated_client, token, currency)

        assert retry.status_code == 302
        assert Room.objects.filter(name="Kilian & Elisabeth").count() == 1
