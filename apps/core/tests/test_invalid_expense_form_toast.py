import http
import json

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def carried_toast_messages(client: Client) -> list[str]:
    return [toast["message"] for toast in client.session.get(ToastMiddleware.CARRIED_TOASTS_SESSION_KEY, [])]


class TestInvalidExpenseForm:
    def test_the_toast_only_points_at_the_inline_errors(
        self, authenticated_client: Client, room: Room, user: User
    ) -> None:
        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}), data={"room_slug": room.slug}
        )

        assert response.status_code == http.HTTPStatus.OK
        toasts = json.loads(response.headers["HX-Trigger"])["triggerToast"]
        assert [toast["message"] for toast in toasts] == ["Please fix the highlighted fields."]
        assert "This field is required" in response.content.decode()
