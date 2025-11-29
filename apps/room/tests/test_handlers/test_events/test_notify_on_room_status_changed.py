from django.urls import reverse

from apps.room.handlers.events.notify_on_room_status_changed import send_notification_on_room_status_changed
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room


def _build_notification_stub(record: list):
    class DummyNotification:
        class Payload:
            def __init__(self, head: str, body: str):
                self.head = head
                self.body = body
                self.click_url = ""

        def __init__(self, payload: Payload):
            self.payload = payload

        def send_to_user(self, user):
            record.append((self, user))

    return DummyNotification


def test_notification_sent_when_room_closes(room: Room, user, guest_user, monkeypatch):
    notifications = []
    monkeypatch.setattr(
        "apps.room.handlers.events.notify_on_room_status_changed.Notification",
        _build_notification_stub(notifications),
    )

    room.lastmodified_by = user
    room.status = Room.StatusChoices.CLOSED
    room.save()

    send_notification_on_room_status_changed(RoomStatusChanged.Context(room=room))

    assert len(notifications) == 1
    notification, recipient = notifications[0]
    assert recipient == guest_user
    assert notification.payload.head == "Room closed"
    expected_url = reverse("room:detail", kwargs={"room_slug": room.slug})
    assert notification.payload.click_url == expected_url


def test_notification_sent_when_room_reopens(room: Room, user, guest_user, monkeypatch):
    notifications = []
    monkeypatch.setattr(
        "apps.room.handlers.events.notify_on_room_status_changed.Notification",
        _build_notification_stub(notifications),
    )

    room.lastmodified_by = user
    room.status = Room.StatusChoices.OPEN
    room.save()

    send_notification_on_room_status_changed(RoomStatusChanged.Context(room=room))

    assert len(notifications) == 1
    notification, recipient = notifications[0]
    assert recipient == guest_user
    assert notification.payload.head == "Room re-opened"
    expected_url = reverse("room:detail", kwargs={"room_slug": room.slug})
    assert notification.payload.click_url == expected_url
