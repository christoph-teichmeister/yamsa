import pytest
from django_pony_express.services.tests import EmailTestService

from apps.account.tests.factories import UserFactory
from apps.room.models import UserConnectionToRoom
from apps.room.tests.factories import RoomFactory
from apps.webpush.services.notification_send_test_service import NotificationSendTestService


@pytest.mark.django_db
class TestNotifyOnUserConnectionToRoomCreated:
    @pytest.fixture(autouse=True)
    def clear_services(self):
        self.email_test_service = EmailTestService()
        self.email_test_service.empty()

        self.notification_test_service = NotificationSendTestService()
        self.notification_test_service.empty()

    def test_creator_of_room_does_not_receive_an_email_when_creating_room(self, user):
        # A fresh room: the user is not connected to it yet, so the connection is a new one.
        UserConnectionToRoom.objects.create(user=user, room=RoomFactory(created_by=user), created_by=user)

        assert self.email_test_service.all().count() == 0
        assert len(self.notification_test_service.all()) == 0

    def test_registered_user_invited_to_room_receives_an_email(self, room, user):
        another_user = UserFactory()
        UserConnectionToRoom.objects.create(user=another_user, room=room, created_by=user)

        assert len(self.notification_test_service.all()) == 1
        assert len(self.notification_test_service.filter(user=another_user)) == 1

        assert self.email_test_service.all().count() == 1
        assert self.email_test_service.filter(to=another_user.email).count() == 1

    def test_no_email_is_sent_when_a_guest_is_invited_to_room(self, guest_user, user):
        UserConnectionToRoom.objects.create(user=guest_user, room=RoomFactory(created_by=user), created_by=user)

        assert self.email_test_service.all().count() == 0
        assert len(self.notification_test_service.all()) == 0

    def test_notification_body_is_localized_to_the_invited_users_language(self, room, user):
        another_user = UserFactory(language="de")
        UserConnectionToRoom.objects.create(user=another_user, room=room, created_by=user)

        notifications = self.notification_test_service.filter(user=another_user)
        assert len(notifications) == 1
        assert notifications[0].payload.head == "Neuer Raum"
        assert notifications[0].payload.body == f"Du wurdest zu {room.name} hinzugefügt!"
