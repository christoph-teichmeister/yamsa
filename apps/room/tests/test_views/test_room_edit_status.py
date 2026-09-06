import pytest
from django.urls import reverse

from apps.room.models import Room

pytestmark = pytest.mark.django_db

OPEN_LABEL = str(Room.StatusChoices.OPEN.label)


class TestRoomEditStatus:
    def test_the_room_edit_page_shows_the_status_label(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:edit", kwargs={"room_slug": room.slug})).content.decode()

        assert f'<h5 class="fw-semibold mb-2">{OPEN_LABEL}</h5>' in content
