import http

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRoomDashboardGuestOnboarding:
    def test_guest_dashboard_shows_onboarding_prompts(self, client, room):
        response = client.get(reverse("room:dashboard", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert "Who are you?" in content
        assert "Maybe register?" in content
        assert "Create a free account" in content
