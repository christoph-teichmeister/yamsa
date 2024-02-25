from time import time

from freezegun import freeze_time

from apps.core.tests.setup import BaseTestSetUp


class UserModelTestCase(BaseTestSetUp):
    def test_str_method(self):
        self.assertEqual(self.user.__str__(), self.user.name)

    @freeze_time("2020-04-04 04:20:00")
    def test_clean_for_guests(self):
        timestamp = time()

        username_before = self.guest_user.username
        email_before = self.guest_user.email
        password_before = self.guest_user.password

        self.guest_user.clean()

        self.assertNotEqual(username_before, self.guest_user.username)
        self.assertNotEqual(email_before, self.guest_user.email)
        self.assertNotEqual(password_before, self.guest_user.password)

        self.assertEqual(self.guest_user.username, f"{self.guest_user.name}-{timestamp}")
        self.assertEqual(self.guest_user.email, f"{self.guest_user.username}@local.local")
        self.assertEqual(self.guest_user.password, f"{self.guest_user.name}-{timestamp}")

    def test_clean_for_regular_user(self):
        username_before = self.user.username
        email_before = self.user.email
        password_before = self.user.password

        self.user.clean()

        self.assertEqual(username_before, self.user.username)
        self.assertEqual(email_before, self.user.email)
        self.assertEqual(password_before, self.user.password)

    def test_room_qs_for_list(self):
        pass

    def test_has_seen_room(self):
        pass

    def test_can_be_removed_from_room(self):
        pass

    def test_generate_random_password_with_length(self):
        pass
