import uuid

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room


@pytest.mark.django_db
class TestRoomCreateView:
    @pytest.fixture
    def owner(self) -> User:
        return UserFactory(is_guest=False)

    @pytest.fixture
    def owner_client(self, client: Client, owner: User) -> Client:
        client.force_login(owner)
        return client

    def test_back_button_targets_dashboard(self, owner_client: Client) -> Client:
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

    def test_second_post_with_same_token_creates_no_second_room(self, owner_client: Client) -> None:
        currency = CurrencyFactory()
        data = {
            "name": "Trip",
            "description": "Weekend",
            "preferred_currency": currency.id,
            "creation_token": str(uuid.uuid4()),
        }

        first = owner_client.post(reverse("room:create"), data)
        second = owner_client.post(reverse("room:create"), data)

        assert Room.objects.filter(name="Trip").count() == 1
        assert first.status_code == second.status_code == 302
        assert first.url == second.url

    def test_posts_with_different_tokens_create_separate_rooms(self, owner_client: Client) -> None:
        currency = CurrencyFactory()
        data = {"name": "Trip", "description": "Weekend", "preferred_currency": currency.id}

        owner_client.post(reverse("room:create"), {**data, "creation_token": str(uuid.uuid4())})
        owner_client.post(reverse("room:create"), {**data, "creation_token": str(uuid.uuid4())})

        assert Room.objects.filter(name="Trip").count() == 2

    def test_form_carries_token_and_disable_on_submit(self, owner_client: Client) -> None:
        content = owner_client.get(reverse("room:create")).content.decode()

        assert 'name="creation_token"' in content or "name=creation_token" in content
        assert "data-disable-on-submit" in content
