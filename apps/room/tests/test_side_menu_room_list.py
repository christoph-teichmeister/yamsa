import re

import pytest
from django.template.loader import render_to_string

from apps.account.context_processors import user_context
from apps.room.models import Room

pytestmark = pytest.mark.django_db

OPEN_LABEL = str(Room.StatusChoices.OPEN.label)
CLOSED_LABEL = str(Room.StatusChoices.CLOSED.label)


def render_side_menu(request):
    return render_to_string("_side_menu_room_list.html", {**user_context(request), "request": request})


def element_classes(html: str, hook: str, text: str) -> str:
    """The class attribute of the one element carrying `hook` and exactly `text`.

    Asserting the whole attribute would break on every utility added next to the hook, which is
    what these rows are built from.
    """
    match = re.search(rf'class="([^"]*\b{re.escape(hook)}\b[^"]*)"[^>]*>{re.escape(text)}<', html)
    assert match is not None, f"no element with .{hook} rendering {text!r}"
    return match.group(1)


class TestSideMenuRoomList:
    def test_open_room_shows_its_status_label(self, rf, user, room):
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert "room-status-badge" in element_classes(html, "room-status-badge", OPEN_LABEL)

    def test_closed_room_shows_its_status_label_in_the_danger_tone(self, rf, user, closed_room):
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert "bg-danger-soft" in element_classes(html, "room-status-badge", CLOSED_LABEL)

    def test_a_room_without_description_falls_back_to_the_status_label(self, rf, user, room):
        # Bypasses full_clean: description is a non-blank field, so an empty value can only
        # come from data that predates that rule.
        Room.objects.filter(pk=room.pk).update(description="")
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert element_classes(html, "room-description", OPEN_LABEL) == "room-description"

    def test_the_name_column_can_shrink_below_the_room_name(self, rf, user, room):
        # Without min-width the column keeps its longest word and pushes the row past the menu
        # panel, which turns the whole side menu into a horizontal scroller.
        request = rf.get("/welcome/")
        request.user = user

        html = render_side_menu(request)

        assert '<div class="room-entry-text min-w-0 flex-1 text-left">' in html
