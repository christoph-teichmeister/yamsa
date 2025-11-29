import pytest
from django.urls import reverse

from apps.account.models import UserFriendship
from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room, UserConnectionToRoom


@pytest.mark.django_db
class TestSuggestedGuestViews:
    @pytest.fixture
    def creator(self):
        return UserFactory(is_guest=False)

    @pytest.fixture
    def collaborator(self):
        return UserFactory(is_guest=False)

    @pytest.fixture
    def currency(self):
        return CurrencyFactory()

    @pytest.fixture
    def room(self, creator, collaborator, currency):
        room_instance = Room.objects.create(
            name="Group Trip",
            description="Desc",
            preferred_currency=currency,
            created_by=creator,
        )
        UserConnectionToRoom.objects.create(user=creator, room=room_instance)
        UserConnectionToRoom.objects.create(user=collaborator, room=room_instance)
        return room_instance

    @pytest.fixture
    def creator_client(self, client, creator):
        client.force_login(creator)
        return client

    def test_room_create_view_injects_suggestions(self, creator_client, room, collaborator):
        response = creator_client.get(reverse("room:create"))
        assert response.status_code == 200
        suggestions = response.context.get("suggested_guests", [])
        assert any(guest.user_id == collaborator.id for guest in suggestions)

    def test_friend_toggle_view_flips_state(self, creator_client, room, collaborator, creator):
        url = reverse("room:htmx-suggested-guest-friend-toggle")
        response = creator_client.post(url, {"suggested_user_id": collaborator.id})
        assert response.status_code == 200
        assert UserFriendship.objects.filter(user=creator, friend=collaborator).exists()
        assert "Friend" in response.content.decode()

        response = creator_client.post(url, {"suggested_user_id": collaborator.id})
        assert response.status_code == 200
        assert not UserFriendship.objects.filter(user=creator, friend=collaborator).exists()

    def test_existing_room_view_includes_suggestions(self, creator_client, room, collaborator):
        url = reverse("room:userconnectiontoroom-create", kwargs={"room_slug": room.slug})
        response = creator_client.get(url)

        assert response.status_code == 200
        suggestions = response.context.get("suggested_guests", [])
        assert any(guest.user_id == collaborator.id for guest in suggestions)
