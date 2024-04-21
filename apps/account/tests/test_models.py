from time import time

from freezegun import freeze_time
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom


class UserModelTestCase(BaseTestSetUp):
    def test_str_method(self):
        self.assertEqual(self.user.__str__(), self.user.name)

    @freeze_time("2020-04-04 04:20:00")
    def test_clean_for_guests(self):
        timestamp = time()

        name_before = self.guest_user.name
        email_before = self.guest_user.email
        password_before = self.guest_user.password

        self.guest_user.clean()

        self.assertEqual(name_before, self.guest_user.name)
        self.assertNotEqual(email_before, self.guest_user.email)
        self.assertNotEqual(password_before, self.guest_user.password)

        self.assertEqual(self.guest_user.email, f"{self.guest_user.name}-{timestamp}@local.local")
        self.assertEqual(self.guest_user.password, f"{self.guest_user.name}-{timestamp}")

    def test_clean_for_regular_user(self):
        name_before = self.user.name
        email_before = self.user.email
        password_before = self.user.password

        self.user.clean()

        self.assertEqual(name_before, self.user.name)
        self.assertEqual(email_before, self.user.email)
        self.assertEqual(password_before, self.user.password)

    def test_room_qs_for_list_user(self):
        qs = self.user.room_qs_for_list

        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first()["name"], self.room.name)

    def test_room_qs_for_list_superuser(self):
        baker.make_recipe("apps.room.tests.room")

        qs = self.superuser.room_qs_for_list

        self.assertEqual(qs.count(), 2)

    def test_has_seen_room_true(self):
        connection = UserConnectionToRoom.objects.get(user=self.user)
        connection.user_has_seen_this_room = True
        connection.save()

        found_connection, has_seen_room = self.user.has_seen_room(self.room.id)

        self.assertTrue(has_seen_room)
        self.assertEqual(connection, found_connection)

    def test_has_seen_room_false(self):
        self.room.users.remove(self.user)

        connection, has_seen_room = self.user.has_seen_room(self.room.id)

        self.assertFalse(has_seen_room)
        self.assertIsNone(connection)

    def test_can_be_removed_from_room_true(self):
        self.assertTrue(self.user.can_be_removed_from_room(self.room.id))

    def test_can_be_removed_from_room_false(self):
        baker.make_recipe("apps.transaction.tests.parent_transaction", room=self.room, paid_by=self.user)

        self.assertFalse(self.user.can_be_removed_from_room(self.room.id))

    def test_generate_random_password_with_length(self):
        password_hash_before = self.user.password

        length = 10
        new_password = self.user.generate_random_password_with_length(length)
        self.assertEqual(len(new_password), length)

        self.user.refresh_from_db()

        self.assertNotEqual(password_hash_before, self.user.password)
