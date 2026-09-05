import pytest
from django.template.loader import render_to_string
from django.urls import reverse

from apps.account.context_processors import user_context
from apps.room.models import Room

pytestmark = pytest.mark.django_db

OPEN_LABEL = str(Room.StatusChoices.OPEN.label)
CLOSED_LABEL = str(Room.StatusChoices.CLOSED.label)


def render_side_menu(request):
    return render_to_string("_side_menu_room_list.html", {**user_context(request), "request": request})


class TestSideMenuRoomList:
    def test_open_room_shows_its_status_label(self, rf, user, room):
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert f'<span class="badge room-status-badge bg-light text-dark">{OPEN_LABEL}</span>' in html

    def test_closed_room_shows_its_status_label(self, rf, user, closed_room):
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert f"text-danger\">{CLOSED_LABEL}</span>" in html

    def test_a_room_without_description_falls_back_to_the_status_label(self, rf, user, room):
        # Bypasses full_clean: description is a non-blank field, so an empty value can only
        # come from data that predates that rule.
        Room.objects.filter(pk=room.pk).update(description="")
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert f'<small class="room-description text-muted">{OPEN_LABEL}</small>' in html


class TestRoomEditStatus:
    def test_the_room_edit_page_shows_the_status_label(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:edit", kwargs={"room_slug": room.slug})).content.decode()

        assert f'<h5 class="fw-semibold mb-2">{OPEN_LABEL}</h5>' in content
