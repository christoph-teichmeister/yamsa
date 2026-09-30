import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory


@pytest.mark.django_db
class TestRoomCreateView:
    @pytest.fixture
    def owner(self) -> User:
        return UserFactory(is_guest=False)

    @pytest.fixture
    def owner_client(self, client, owner) -> Client:
        client.force_login(owner)
        return client

    def test_back_button_targets_dashboard(self, owner_client) -> None:
        response = owner_client.get(reverse("room:create"))

        assert response.status_code == 200
        content = response.content.decode()
        dashboard_url = reverse("core:welcome")
        href_fragment = f'href="{dashboard_url}"'
        href_fragment_unquoted = f"href={dashboard_url}"
        hx_get_fragment = f'hx-get="{dashboard_url}"'
        hx_get_fragment_unquoted = f"hx-get={dashboard_url}"

        # An href as well as the hx-get: the link has to work when the bundle never runs.
        assert href_fragment in content or href_fragment_unquoted in content
        assert hx_get_fragment in content or hx_get_fragment_unquoted in content
        assert "Back to dashboard" in content
