import http
import json
import uuid

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


def carried_toast_messages(client: Client) -> list[str]:
    return [toast["message"] for toast in client.session.get(ToastMiddleware.CARRIED_TOASTS_SESSION_KEY, [])]


class TestSuccessToasts:
    def test_deleting_an_expense_confirms(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(user, guest_user)
        )

        authenticated_client.post(
            reverse(
                "transaction:parent-transaction-delete", kwargs={"room_slug": room.slug, "pk": parent_transaction.pk}
            )
        )

        assert carried_toast_messages(authenticated_client) == ["Expense deleted."]

    def test_settling_a_debt_confirms(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        debt = room.debts.filter(settled=False).first()
        authenticated_client.force_login(guest_user)

        authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.pk}), data={"settled": "on"}
        )

        assert carried_toast_messages(authenticated_client) == ["Debt marked as settled."]

    def test_creating_a_room_confirms(self, authenticated_client: Client) -> None:
        response = authenticated_client.post(
            reverse("room:create"),
            {
                "name": "Trip",
                "description": "Weekend",
                "preferred_currency": CurrencyFactory().id,
                "creation_token": str(uuid.uuid4()),
            },
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert carried_toast_messages(authenticated_client) == ["Room created."]

    def test_removing_a_member_confirms(self, authenticated_client: Client, room: Room, guest_user: User) -> None:
        response = authenticated_client.post(
            reverse("account:remove-from-room", kwargs={"room_slug": room.slug, "pk": guest_user.id}),
            headers={"HX-Request": "true"},
            follow=True,
        )

        toasts = json.loads(response.headers["HX-Trigger-After-Settle"])["triggerToast"]
        assert [toast["message"] for toast in toasts] == [f'"{guest_user.name}" was removed from the room.']
