from django_pony_express.services.tests import EmailTestService
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom
from apps.webpush.services.notification_send_test_service import NotificationSendTestService


class NotifyOnUserConnectionToRoomCreatedTestCase(BaseTestSetUp):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.email_test_service = EmailTestService()
        cls.notification_test_service = NotificationSendTestService()

    def test_creator_of_room_does_not_receive_an_email_when_creating_room(self):
        UserConnectionToRoom.objects.create(user=self.user, room=self.room, created_by=self.user)

        self.assertEqual(self.email_test_service.all().count(), 0)
        self.assertEqual(len(self.notification_test_service.all()), 0)

    def test_registered_user_invited_to_room_receives_an_email(self):
        another_user = baker.make_recipe("apps.account.tests.user")
        UserConnectionToRoom.objects.create(user=another_user, room=self.room, created_by=self.user)

        self.assertEqual(len(self.notification_test_service.all()), 1)
        self.assertEqual(len(self.notification_test_service.filter(user=another_user)), 1)

        self.assertEqual(self.email_test_service.all().count(), 1)
        self.assertEqual(self.email_test_service.filter(to=another_user.email).count(), 1)

    def test_no_email_is_sent_when_a_guest_is_invited_to_room(self):
        UserConnectionToRoom.objects.create(user=self.guest_user, room=self.room, created_by=self.user)

        self.assertEqual(self.email_test_service.all().count(), 0)
        self.assertEqual(len(self.notification_test_service.all()), 0)
