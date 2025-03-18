from unittest import mock

from ambient_toolbox.middleware.current_request import CurrentRequestMiddleware
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import UserConnectionToRoom


class GuestSendInvitationEmailFormTestCase(BaseTestSetUp):
    form_class = UserConnectionToRoomCreateForm

    def test_create_regular(self):
        new_room = baker.make_recipe("apps.room.tests.room")
        data = {"email": self.user.email, "room_slug": new_room.slug}

        self.assertFalse(UserConnectionToRoom.objects.filter(user=self.user, room=new_room).exists())

        form = self.form_class(data=data)
        self.assertTrue(form.is_valid())

        with mock.patch.object(CurrentRequestMiddleware, "get_current_user", return_value=self.user):
            created_userconnectiontoroom = form.save()

        self.assertIsNotNone(created_userconnectiontoroom)

        new_room.refresh_from_db()

        self.assertTrue(new_room.users.filter(email=self.user.email).exists())

    def test_clean_email_regular(self):
        new_room = baker.make_recipe("apps.room.tests.room")
        data = {"email": self.user.email, "room_slug": new_room.slug}

        form = self.form_class(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_email_raises_email_unknown_error(self):
        room_slug = "a-room-slug"
        email_address = "this_address_does_not_exist@local.local"
        data = {"email": email_address, "room_slug": room_slug}

        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"][0], form.ExceptionMessage.EMAIL_UNKNOWN)

    def test_form_raises_error_if_user_already_in_room(self):
        data = {"email": self.user.email, "room_slug": self.room.slug}

        form = self.form_class(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"][0], form.ExceptionMessage.EMAIL_ALREADY_IN_ROOM, form.errors)
