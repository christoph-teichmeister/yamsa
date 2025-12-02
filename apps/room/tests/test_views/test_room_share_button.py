import pytest
from django.urls import reverse

from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory, UserConnectionToRoomFactory


@pytest.mark.django_db
class TestRoomShareButton:
    @pytest.fixture
    def owner(self):
        return UserFactory(is_guest=False)

    @pytest.fixture
    def currency(self):
        return CurrencyFactory()

    @pytest.fixture
    def room(self, owner, currency):
        room = RoomFactory(
            name="Trip Space",
            description="Group",
            preferred_currency=currency,
            created_by=owner,
        )
        UserConnectionToRoomFactory(user=owner, room=room)
        return room

    @pytest.fixture
    def owner_client(self, client, owner):
        client.force_login(owner)
        return client

    def test_share_button_shows_for_open_rooms_without_guests(self, owner_client, room):
        response = owner_client.get(reverse("room:dashboard", kwargs={"room_slug": room.slug}))

        assert response.status_code == 200
        assert "data-copy-share-url" in response.content.decode()

    def test_share_button_shows_for_open_room_with_guests(self, owner_client, room):
        guest = GuestUserFactory()
        UserConnectionToRoomFactory(user=guest, room=room)

        response = owner_client.get(reverse("room:dashboard", kwargs={"room_slug": room.slug}))

        assert response.status_code == 200
        assert "data-copy-share-url" in response.content.decode()

    def test_share_button_hides_when_room_closed(self, owner_client, room):
        room.status = Room.StatusChoices.CLOSED
        room.save(update_fields=["status"])

        response = owner_client.get(reverse("room:dashboard", kwargs={"room_slug": room.slug}))

        assert response.status_code == 200
        content = response.content.decode()
        assert "data-copy-share-url" not in content
        assert "bi-dash-circle" in content

    def test_who_are_you_partial_calls_out_registration_cta(self, owner_client, room):
        owner_client.logout()
        guest = GuestUserFactory()
        UserConnectionToRoomFactory(user=guest, room=room)

        response = owner_client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Claim your invitation" in content
        assert "Create a free account" in content

    def test_who_are_you_without_guests_promotes_account_creation(self, owner_client, room):
        owner_client.logout()

        response = owner_client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))

        assert response.status_code == 200
        content = response.content.decode()
        assert "No guests have been invited yet" in content
        assert 'name="user_id"' not in content
