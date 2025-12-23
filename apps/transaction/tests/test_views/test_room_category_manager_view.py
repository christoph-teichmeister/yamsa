import http

import pytest
from django.urls import reverse

from apps.transaction.models import Category, RoomCategory

pytestmark = pytest.mark.django_db


class TestRoomCategoryManagerView:
    def test_owner_can_access_manager(self, authenticated_client, room):
        response = authenticated_client.get(reverse("transaction:category-manager", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        assert "Manage categories" in response.content.decode()

    def test_guest_cannot_access_manager(self, client, guest_user, room):
        client.force_login(guest_user)
        response = client.get(reverse("transaction:category-manager", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_owner_can_create_category(self, authenticated_client, room):
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        payload = {
            "action": "create",
            "name": "Room Tag",
            "emoji": "🚀",
            "color": "#ABCDEF",
            "make_default": "true",
        }
        response = authenticated_client.post(url, data=payload, HTTP_HX_REQUEST="true")

        assert response.status_code == http.HTTPStatus.OK
        RoomCategory.objects.filter(room=room).exists()
        category = Category.objects.get(name="Room Tag")
        assert RoomCategory.objects.filter(room=room, category=category).exists()
        assert RoomCategory.objects.get(room=room, category=category).is_default
