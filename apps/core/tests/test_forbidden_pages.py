import http
import json

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.room.models import Room
from apps.transaction.models.constants import FORMER_MEMBER_MESSAGE
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


def carried_toast_messages(client: Client) -> list[str]:
    return [toast["message"] for toast in client.session.get(ToastMiddleware.CARRIED_TOASTS_SESSION_KEY, [])]


class TestForbiddenPages:
    def test_a_non_member_gets_the_styled_403_page(self, client: Client, room: Room) -> None:
        stranger = UserFactory()
        client.force_login(stranger)

        response = client.get(reverse("transaction:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert "You are not allowed to see this page" in response.content.decode()

    def test_a_closed_room_names_itself_in_an_htmx_toast(self, authenticated_client: Client, closed_room: Room) -> None:
        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": closed_room.slug}), headers={"HX-Request": "true"}
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        toasts = json.loads(response.headers["HX-Trigger"])["triggerToast"]
        assert toasts[0]["message"] == "This room is closed. No changes can be made."

    def test_a_former_member_transaction_explains_itself(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room, paid_by=guest_user, paid_for_tuple=(user, guest_user)
        )
        room.users.remove(guest_user)

        response = authenticated_client.get(
            reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent_transaction.pk})
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert str(FORMER_MEMBER_MESSAGE) in response.content.decode()
