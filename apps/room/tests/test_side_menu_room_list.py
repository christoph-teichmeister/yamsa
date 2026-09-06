import pytest
from django.template.loader import render_to_string

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

        assert f'<span class="badge room-status-badge bg-body-secondary text-body-emphasis">{OPEN_LABEL}</span>' in html

    def test_closed_room_shows_its_status_label(self, rf, user, closed_room):
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert f'text-danger">{CLOSED_LABEL}</span>' in html

    def test_a_room_without_description_falls_back_to_the_status_label(self, rf, user, room):
        # Bypasses full_clean: description is a non-blank field, so an empty value can only
        # come from data that predates that rule.
        Room.objects.filter(pk=room.pk).update(description="")
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert f'<small class="room-description text-muted">{OPEN_LABEL}</small>' in html

    def test_the_name_column_can_shrink_below_the_room_name(self, rf, user, room):
        # Without room-entry-text the column keeps its longest word and pushes the row past the
        # menu panel, which turns the whole side menu into a horizontal scroller.
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert '<div class="room-entry-text flex-grow-1 text-start">' in html
