import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.constants import SHARED_ROOM_SLUG_SESSION_KEY
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory, UserConnectionToRoomFactory


@pytest.mark.django_db
class TestRoomShareView:
    def test_returns_dashboard_for_valid_share_hash(self, client: Client) -> None:
        room = RoomFactory()

        response = client.get(reverse("room:share", kwargs={"share_hash": room.share_hash}))

        assert response.status_code == 200
        response.render()
        assert response.wsgi_request.room == room
        assert any(template.name == "room/dashboard.html" for template in response.templates if template.name)

    def test_returns_404_for_invalid_share_hash(self, client: Client) -> None:
        response = client.get(reverse("room:share", kwargs={"share_hash": "missing123"}))

        assert response.status_code == 404

    @pytest.fixture
    def owner(self) -> User:
        return UserFactory(is_guest=False)

    @pytest.fixture
    def room_with_owner(self, owner: User) -> Room:
        room = RoomFactory(created_by=owner)
        UserConnectionToRoomFactory(user=owner, room=room)
        return room

    def test_authenticated_room_member_redirects_to_transaction_list(
        self, client: Client, room_with_owner: Room, owner: User
    ) -> None:
        client.force_login(owner)

        response = client.get(reverse("room:share", kwargs={"share_hash": room_with_owner.share_hash}))

        assert response.status_code == 302
        assert response.url == reverse("transaction:list", kwargs={"room_slug": room_with_owner.slug})

    def test_authenticated_non_member_sees_dashboard(self, client: Client, room_with_owner: Room) -> None:
        non_member = UserFactory(email="nonmember@example.com", name="Non Member")
        client.force_login(non_member)

        response = client.get(reverse("room:share", kwargs={"share_hash": room_with_owner.share_hash}))

        assert response.status_code == 200
        response.render()
        assert any(template.name == "room/dashboard.html" for template in response.templates if template.name)

    def test_share_slug_saved_in_session(self, client: Client, room_with_owner: Room) -> None:
        response = client.get(reverse("room:share", kwargs={"share_hash": room_with_owner.share_hash}))

        assert response.status_code == 200
        assert response.wsgi_request.session.get(SHARED_ROOM_SLUG_SESSION_KEY) == str(room_with_owner.slug)

    def test_returns_404_for_deleted_room(self, client: Client) -> None:
        room = RoomFactory()
        share_hash = room.share_hash
        room.news.all().delete()

        room.delete()
        response = client.get(reverse("room:share", kwargs={"share_hash": share_hash}))

        assert response.status_code == 404
