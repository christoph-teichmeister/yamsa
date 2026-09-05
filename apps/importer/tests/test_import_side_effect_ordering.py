from unittest import mock

import pytest
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.importer.tests.factories import build_upload
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.models import ParentTransaction

ROWS = [
    "2023-02-28,Cambio,Allgemein,25.20,EUR,-25.20,25.20",
    "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
]


class TestImportSideEffectOrdering:
    """
    handle_event re-raises, so a failing notification aborts everything after it. The debt
    recalculation must therefore run before the connection mails, not after.
    """

    def _import(self, client, currency, friend):
        redirect = client.post(reverse("importer:upload"), data={"source": "splitwise-csv", "file": build_upload(ROWS)})
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
            "person_1": f"user-{friend.pk}",
        }
        for index, category in enumerate(form.parsed.categories):
            payload[f"category_{index}"] = category.suggested_slug
        return client.post(reverse("importer:preview"), data=payload)

    @pytest.fixture
    def friend(self, db, user, room):
        existing = UserFactory(name="Elisabeth")
        room.users.add(existing)
        return existing

    def test_debts_survive_a_failing_connection_mail(self, db, authenticated_client, currency, friend):
        target = "apps.mail.services.user_added_to_room_mail_service.UserAddedToRoomEmailService.process"
        with mock.patch(target, side_effect=OSError("SMTP down")), pytest.raises(OSError):
            self._import(authenticated_client, currency, friend)

        imported_room = Room.objects.get(name="Kilian & Elisabeth")
        assert ParentTransaction.objects.filter(room=imported_room).count() == 2
        # The whole point: the room is not left with transactions and no debts.
        assert Debt.objects.filter(room=imported_room, settled=False).exists()

    def test_a_healthy_import_connects_everyone(self, db, authenticated_client, currency, friend):
        response = self._import(authenticated_client, currency, friend)

        imported_room = Room.objects.get(name="Kilian & Elisabeth")
        assert response.status_code == 302
        assert UserConnectionToRoom.objects.filter(room=imported_room, user=friend).exists()
        assert imported_room.users.count() == 2
