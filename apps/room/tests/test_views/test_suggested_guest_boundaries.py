import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User, UserFriendship
from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room, UserConnectionToRoom
from apps.room.tests.factories import RoomFactory, UserConnectionToRoomFactory


@pytest.mark.django_db
class TestSuggestedGuestBoundaries:
    @pytest.fixture
    def creator(self) -> User:
        return UserFactory(is_guest=False)

    @pytest.fixture
    def collaborator(self, creator: User) -> User:
        collaborator = UserFactory(is_guest=False)
        shared_room = RoomFactory(created_by=creator)
        UserConnectionToRoomFactory(user=creator, room=shared_room)
        UserConnectionToRoomFactory(user=collaborator, room=shared_room)
        return collaborator

    @pytest.fixture
    def creator_client(self, client: Client, creator: User) -> Client:
        client.force_login(creator)
        return client

    def _create_room(self, client: Client, emails: list[str]) -> object:
        return client.post(
            reverse("room:create"),
            {
                "name": "Trip",
                "description": "Weekend",
                "preferred_currency": CurrencyFactory().id,
                "suggested_guest_emails": emails,
            },
        )

    def test_a_suggested_person_is_added(self, creator_client: Client, collaborator: User) -> None:
        self._create_room(creator_client, [collaborator.email])

        room = Room.objects.get(name="Trip")
        assert UserConnectionToRoom.objects.filter(room=room, user=collaborator).exists()

    def test_an_address_that_was_never_suggested_is_not_added(self, creator_client: Client, creator: User) -> None:
        stranger = UserFactory(is_guest=False)

        self._create_room(creator_client, [stranger.email])

        room = Room.objects.get(name="Trip")
        assert list(room.users.all()) == [creator]

    def test_skipped_people_are_reported(self, creator_client: Client) -> None:
        response = self._create_room(creator_client, ["nobody@example.com"])

        landing = creator_client.get(response.url)
        assert "could not be added to the room" in landing.content.decode()

    @pytest.mark.parametrize("bad_id", ["abc", "999999", ""])
    def test_friend_toggle_answers_every_bad_id_alike(self, creator_client: Client, bad_id: str) -> None:
        response = creator_client.post(
            reverse("room:htmx-suggested-guest-friend-toggle"), {"suggested_user_id": bad_id}
        )

        assert response.status_code == 400

    def test_friend_toggle_refuses_a_stranger(self, creator_client: Client, creator: User) -> None:
        stranger = UserFactory(is_guest=False)

        response = creator_client.post(
            reverse("room:htmx-suggested-guest-friend-toggle"), {"suggested_user_id": stranger.id}
        )

        assert response.status_code == 400
        assert not UserFriendship.objects.filter(user=creator, friend=stranger).exists()
