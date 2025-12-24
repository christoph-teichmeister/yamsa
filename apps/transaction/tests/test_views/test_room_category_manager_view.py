import http
import json

import pytest
from django.urls import reverse

from apps.transaction.models import Category, RoomCategory
from apps.transaction.services.room_category_service import RoomCategoryService

pytestmark = pytest.mark.django_db


class TestRoomCategoryManagerView:
    def test_owner_can_access_manager(self, authenticated_client, room):
        response = authenticated_client.get(reverse("transaction:category-manager", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        assert "Manage categories" in response.content.decode()

    def test_guest_member_can_access_manager(self, client, guest_user, room):
        client.force_login(guest_user)
        response = client.get(reverse("transaction:category-manager", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        assert "Manage categories" in response.content.decode()

    def test_non_member_cannot_access_manager(self, client, room):
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
        assert RoomCategory.objects.filter(room=room).exists()
        category = Category.objects.get(name="Room Tag")
        assert RoomCategory.objects.filter(room=room, category=category).exists()
        assert RoomCategory.objects.get(room=room, category=category).is_default

    def test_create_invalid_form_returns_error_fragment(self, authenticated_client, room):
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        payload = {
            "action": "create",
            "name": "Room Tag",
            "emoji": "not-an-emoji",
            "color": "#ABCDEF",
        }

        response = authenticated_client.post(url, data=payload, HTTP_HX_REQUEST="true")

        assert response.status_code == http.HTTPStatus.OK
        assert "Enter a single emoji character." in response.content.decode()
        assert not RoomCategory.objects.filter(room=room, category__name="Room Tag").exists()

    def test_create_without_htmx_redirects(self, client, user, room):
        client.force_login(user)
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        payload = {
            "action": "create",
            "name": "Orderly Room",
            "emoji": "✨",
            "color": "#112233",
        }

        response = client.post(url, data=payload)

        assert response.status_code == http.HTTPStatus.FOUND
        assert response["Location"] == url

    def test_update_category_reorders_on_htmx_request(self, authenticated_client, room):
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        service = RoomCategoryService(room=room)
        target = service.create_room_category(name="Custom Order", emoji="🎯", color="#123456")

        response = authenticated_client.post(
            url,
            data={
                "action": "update",
                "room_category_id": target.pk,
                "order_index": "0",
                "make_default": "false",
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        target.refresh_from_db()
        assert target.order_index == 0

    def test_update_invalid_form_adds_error_toast(self, authenticated_client, room):
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        target = RoomCategoryService(room=room).get_categories()[0]

        response = authenticated_client.post(
            url,
            data={
                "action": "update",
                "room_category_id": target.pk,
                "order_index": "-1",
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert "Ensure this value is greater than or equal to 0." in response.content.decode()
        trigger_payload = json.loads(response["HX-Trigger"])
        assert (
            trigger_payload["triggerToast"][0]["message"]
            == "Unable to update that category. Please correct the highlighted fields."
        )

    def test_delete_category_emits_success_toast(self, authenticated_client, room):
        url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        service = RoomCategoryService(room=room)
        target = service.create_room_category(name="Temporary", emoji="🧹", color="#123123")

        response = authenticated_client.post(
            url,
            data={"action": "delete", "room_category_id": target.pk},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert not RoomCategory.objects.filter(pk=target.pk).exists()
        trigger_payload = json.loads(response["HX-Trigger"])
        assert trigger_payload["triggerToast"][0]["message"] == f'Category "{target.category.name}" deleted.'
