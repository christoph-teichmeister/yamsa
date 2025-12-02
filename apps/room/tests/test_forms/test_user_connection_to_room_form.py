from unittest import mock

import pytest
from ambient_toolbox.middleware.current_request import CurrentRequestMiddleware

from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import UserConnectionToRoom
from apps.room.tests.factories import RoomFactory


@pytest.mark.django_db
class TestUserConnectionToRoomCreateForm:
    form_class = UserConnectionToRoomCreateForm

    def test_create_regular(self, user):
        new_room = RoomFactory(created_by=user)
        data = {"email": user.email, "room_slug": new_room.slug}

        assert not UserConnectionToRoom.objects.filter(user=user, room=new_room).exists()

        form = self.form_class(data=data)
        assert form.is_valid()

        with mock.patch.object(CurrentRequestMiddleware, "get_current_user", return_value=user):
            created_userconnectiontoroom = form.save()

        assert created_userconnectiontoroom is not None
        new_room.refresh_from_db()
        assert new_room.users.filter(email=user.email).exists()

    def test_clean_email_regular(self, user):
        new_room = RoomFactory(created_by=user)
        data = {"email": user.email, "room_slug": new_room.slug}
        form = self.form_class(data=data)

        assert form.is_valid(), form.errors

    def test_clean_email_raises_email_unknown_error(self):
        data = {
            "email": "this_address_does_not_exist@local.local",
            "room_slug": "a-room-slug",
        }

        form = self.form_class(data=data)
        assert not form.is_valid()
        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_UNKNOWN

    def test_form_raises_error_if_user_already_in_room(self, user, room):
        data = {"email": user.email, "room_slug": room.slug}
        form = self.form_class(data=data)

        assert not form.is_valid()
        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_ALREADY_IN_ROOM
