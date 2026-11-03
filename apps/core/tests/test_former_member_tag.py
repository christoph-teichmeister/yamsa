import pytest
from django.template import Context, Template
from django.test import RequestFactory

from apps.account.models import User
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def render(room: Room, user_id: int) -> str:
    request = RequestFactory().get("/")
    request.room = room
    return Template("{% load core_tags %}{% former_member_tag user_id %}").render(
        Context({"request": request, "user_id": user_id})
    )


def test_a_current_member_gets_no_tag(room: Room, user: User) -> None:
    assert "Left" not in render(room, user.id)


def test_a_user_who_left_gets_the_tag(room: Room, guest_user: User) -> None:
    room.users.remove(guest_user)

    assert "Left" in render(room, guest_user.id)
