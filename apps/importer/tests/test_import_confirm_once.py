from unittest import mock

from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.currency.models import Currency
from apps.importer.services.import_service import ImportService
from apps.importer.session import pop_parsed_import, read_parsed_import
from apps.importer.tests.factories import build_upload
from apps.room.models import Room

ROWS = ["2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20"]


class TestImportConfirmOnce:
    """Two confirm POSTs for one token (double click) must create one room, not two."""

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

    def test_payload_is_consumed_before_the_import_starts(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)
        calls: list[str] = []
        real_process = ImportService.process
        real_pop = pop_parsed_import

        def process_spy(service: ImportService, **kwargs: object) -> object:
            calls.append("process")
            return real_process(service, **kwargs)

        def pop_spy(*args: object) -> object:
            calls.append("pop")
            return real_pop(*args)

        with (
            mock.patch("apps.importer.views.import_preview_view.pop_parsed_import", side_effect=pop_spy),
            mock.patch.object(ImportService, "process", autospec=True, side_effect=process_spy),
        ):
            self._confirm(authenticated_client, token, currency)

        assert calls == ["pop", "process"]

    def test_a_replayed_confirm_creates_no_second_room(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)
        form_page = authenticated_client.get(f"{reverse('importer:preview')}?token={token}")
        assert form_page.status_code == 200

        self._confirm(authenticated_client, token, currency)
        replay = authenticated_client.post(reverse("importer:preview"), data={"token": token})

        assert replay.status_code == 302
        assert replay.url == reverse("importer:upload")
        assert Room.objects.filter(name="Kilian & Elisabeth").count() == 1

    def test_a_failed_import_keeps_the_payload_for_a_retry(
        self, db: None, authenticated_client: Client, currency: Currency
    ) -> None:
        token = self._token(authenticated_client)
        authenticated_client.raise_request_exception = False

        with mock.patch.object(ImportService, "process", side_effect=RuntimeError("boom")):
            response = self._confirm(authenticated_client, token, currency)

        assert response.status_code == 500
        assert read_parsed_import(authenticated_client.session, token) is not None
