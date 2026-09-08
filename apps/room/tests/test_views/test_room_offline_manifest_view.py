import json

import pytest
from django.urls import reverse

from apps.core.pwa_constants import PREFETCH_HEADER_NAME
from apps.room.services.dashboard_tab_service import DashboardTabService

pytestmark = pytest.mark.django_db


def _manifest_url(room):
    return reverse("room:offline-manifest", kwargs={"room_slug": room.slug})


def test_manifest_covers_the_rooms_navigation(authenticated_client, room):
    """A tab the manifest misses is a tab that shows the offline page instead of the room."""
    response = authenticated_client.get(_manifest_url(room))

    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["room"] == str(room.slug)

    tab_urls = [tab.get_url for tab in DashboardTabService(room=room).get_tabs_as_list()]
    assert payload["urls"][: len(tab_urls)] == tab_urls


def test_manifest_covers_the_expense_form(authenticated_client, room):
    """The queue for expenses entered in a dead spot is worth nothing without the form."""
    payload = json.loads(authenticated_client.get(_manifest_url(room)).content)

    assert reverse("transaction:create", kwargs={"room_slug": room.slug}) in payload["urls"]


def test_every_listed_url_can_actually_be_fetched(authenticated_client, room):
    """A URL the manifest names but the app refuses would cache the offline page instead."""
    urls = json.loads(authenticated_client.get(_manifest_url(room)).content)["urls"]

    for url in urls:
        response = authenticated_client.get(url, headers={PREFETCH_HEADER_NAME.lower(): "1"})
        assert response.status_code == 200, url


def test_a_non_member_gets_no_manifest(client, room, guest_user):
    """The manifest is the list of pages worth caching, so it may not outline a foreign room."""
    client.force_login(guest_user)
    room.users.remove(guest_user)
    room.userconnectiontoroom_set.filter(user=guest_user).delete()

    assert client.get(_manifest_url(room)).status_code == 403
