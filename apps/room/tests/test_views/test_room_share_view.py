import pytest
from django.urls import reverse

from apps.room.tests.factories import RoomFactory


@pytest.mark.django_db
class TestRoomShareView:
    def test_returns_dashboard_for_valid_share_hash(self, client):
        room = RoomFactory()

        response = client.get(reverse("room:share", kwargs={"share_hash": room.share_hash}))

        assert response.status_code == 200
        response.render()
        assert response.wsgi_request.room == room
        assert any(template.name == "room/dashboard.html" for template in response.templates if template.name)

    def test_returns_404_for_invalid_share_hash(self, client):
        response = client.get(reverse("room:share", kwargs={"share_hash": "missing123"}))

        assert response.status_code == 404

    def test_returns_404_for_deleted_room(self, client):
        room = RoomFactory()
        share_hash = room.share_hash
        room.news.all().delete()

        room.delete()
        response = client.get(reverse("room:share", kwargs={"share_hash": share_hash}))

        assert response.status_code == 404
