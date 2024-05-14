from django_pony_express.services.tests import EmailTestService

from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom


class NotifyOnUserConnectionToRoomCreatedTestCase(BaseTestSetUp):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.email_test_service = EmailTestService()

    def test_test(self):
        UserConnectionToRoom.objects.create(user=self.user, room=self.room, created_by=self.user)

        self.assertEqual(self.email_test_service.filter(to=self.user.email).count(), 0)
