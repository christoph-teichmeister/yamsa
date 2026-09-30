import http

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRoomListRedirect:
    def test_the_legacy_room_list_url_redirects_to_the_dashboard(self, client: Client):
        response = client.get(reverse("room:list"))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url == reverse("core:welcome")
