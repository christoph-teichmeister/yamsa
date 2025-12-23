import pytest
from django.urls import reverse

from apps.account.tests.factories import UserFactory


@pytest.mark.django_db
class TestRoomCreateView:
    @pytest.fixture
    def owner(self):
        return UserFactory(is_guest=False)

    @pytest.fixture
    def owner_client(self, client, owner):
        client.force_login(owner)
        return client

    def test_back_button_targets_room_list(self, owner_client):
        response = owner_client.get(reverse("room:create"))

        assert response.status_code == 200
        content = response.content.decode()
        room_list_url = reverse("room:list")
        href_fragment = f"href={room_list_url}"
        hx_get_fragment = f"hx-get={room_list_url}"

        assert href_fragment in content
        assert hx_get_fragment in content
        assert 'bi-arrow-left' in content
        assert 'Back to rooms' in content
