from typing import Any

import pytest
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.handlers.events.notify_on_room_deleted import send_notification_on_room_deleted
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted


def _build_notification_stub(record: list[tuple[Any, Any]]) -> type:
    class DummyNotification:
        class Payload:
            def __init__(self, head: str, body: str, click_url: str = "") -> None:
                self.head = head
                self.body = body
                self.click_url = click_url

        def __init__(self, payload: "DummyNotification.Payload") -> None:
            self.payload = payload

        def send_to_user(self, user: User) -> None:
            record.append((self, user))

    return DummyNotification


@pytest.mark.django_db
def test_remaining_members_are_notified(guest_user: User, monkeypatch: pytest.MonkeyPatch):
    notifications = []
    monkeypatch.setattr(
        "apps.room.handlers.events.notify_on_room_deleted.Notification",
        _build_notification_stub(notifications),
    )

    send_notification_on_room_deleted(
        RoomHardDeleted.Context(
            room_name="Ski trip",
            actor_name="Alice",
            member_user_ids=[guest_user.id],
            receipt_storage_refs=[],
        )
    )

    assert len(notifications) == 1
    notification, recipient = notifications[0]
    assert recipient == guest_user
    assert notification.payload.head == "Room deleted"
    assert notification.payload.body == 'Alice deleted "Ski trip"'
    assert notification.payload.click_url == reverse("core:welcome")


@pytest.mark.django_db
def test_localizes_the_body_per_recipient_language(monkeypatch: pytest.MonkeyPatch):
    german_speaker = UserFactory(language="de")

    notifications = []
    monkeypatch.setattr(
        "apps.room.handlers.events.notify_on_room_deleted.Notification",
        _build_notification_stub(notifications),
    )

    send_notification_on_room_deleted(
        RoomHardDeleted.Context(
            room_name="Ski trip",
            actor_name="Alice",
            member_user_ids=[german_speaker.id],
            receipt_storage_refs=[],
        )
    )

    _, recipient = notifications[0]
    assert recipient == german_speaker
    assert notifications[0][0].payload.body == 'Alice hat "Ski trip" gelöscht'
