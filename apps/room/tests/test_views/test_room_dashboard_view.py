import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRoomDashboardGuestOnboarding:
    def test_guest_dashboard_shows_onboarding_prompts(self, client, room):
        response = client.get(reverse("room:dashboard", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        soup = BeautifulSoup(response.content, "html.parser")
        assert soup.find(string=lambda text: text and "Who are you?" in text)
        assert soup.find(string=lambda text: text and "Maybe register?" in text)
        assert soup.find(string=lambda text: text and "Create a free account" in text)
