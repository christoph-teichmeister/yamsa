import http
import json

import pytest
from django.urls import reverse

from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.models import User
from apps.account.views import UserListForRoomView
from apps.core.toast_constants import ERROR_TOAST_CLASS
from apps.core.views import WelcomePartialView

pytestmark = pytest.mark.django_db


recorded_messages: list[object] = []


def handle_message(message):
    recorded_messages.append(message)
    return message


def deny_removal(self, room_id):
    return False


def allow_removal(self, room_id):
    return True


@pytest.fixture
def recorded_messages_recorder():
    recorded_messages.clear()
    return recorded_messages


def test_post_user_can_not_be_removed_from_room(
    room,
    guest_user,
    user,
    hx_client,
    monkeypatch,
    recorded_messages_recorder,
):
    room.users.add(guest_user)

    monkeypatch.setattr(
        "apps.account.views.user_remove_from_room_view.handle_message",
        handle_message,
    )
    monkeypatch.setattr(User, "can_be_removed_from_room", deny_removal)

    client = hx_client(user)
    response = client.post(
        reverse(
            "account:remove-from-room",
            kwargs={"room_slug": room.slug, "pk": guest_user.id},
        ),
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert not recorded_messages_recorder

    assert response.template_name[0] == UserListForRoomView.template_name
    payload = json.loads(response.headers["HX-Trigger-After-Settle"])
    toasts = payload["triggerToast"]
    assert isinstance(toasts, list)
    assert toasts[0]["message"] == (
        f'"{guest_user.name}" can not be removed from this room, '
        "because they still have either transactions or open debts."
    )
    assert toasts[0]["type"] == ERROR_TOAST_CLASS


def test_post_user_can_be_removed_from_room(
    room,
    guest_user,
    user,
    hx_client,
    monkeypatch,
    recorded_messages_recorder,
):
    room.users.add(guest_user)

    monkeypatch.setattr(
        "apps.account.views.user_remove_from_room_view.handle_message",
        handle_message,
    )
    monkeypatch.setattr(User, "can_be_removed_from_room", allow_removal)

    client = hx_client(user)
    response = client.post(
        reverse(
            "account:remove-from-room",
            kwargs={"room_slug": room.slug, "pk": guest_user.id},
        ),
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages_recorder) == 1
    assert isinstance(recorded_messages_recorder[0], RemoveUserFromRoom)
    assert response.template_name[0] == UserListForRoomView.template_name


def test_post_user_removes_themselves_from_room(
    room,
    user,
    hx_client,
    monkeypatch,
    recorded_messages_recorder,
):
    room.users.add(user)

    monkeypatch.setattr(
        "apps.account.views.user_remove_from_room_view.handle_message",
        handle_message,
    )
    monkeypatch.setattr(User, "can_be_removed_from_room", allow_removal)

    client = hx_client(user)
    response = client.post(
        reverse(
            "account:remove-from-room",
            kwargs={"room_slug": room.slug, "pk": user.id},
        ),
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages_recorder) == 1
    assert isinstance(recorded_messages_recorder[0], RemoveUserFromRoom)
    assert response.template_name[0] == WelcomePartialView.template_name
