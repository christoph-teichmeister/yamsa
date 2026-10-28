import http
from datetime import UTC, datetime

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, ParentTransaction

pytestmark = pytest.mark.django_db


class TestTransactionCreateRoomIsForced:
    """A posted `room` must never move a transaction out of the room named in the URL."""

    def test_a_posted_foreign_room_is_ignored(self, authenticated_client: Client, room: Room, user: User) -> None:
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user)
        members = list(room.users.all())

        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "category": Category.objects.get(slug="groceries").id,
                "description": "Crafted",
                "currency": room.preferred_currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": user.id,
                "room": other_room.id,
                "paid_for": [str(member.id) for member in members],
                "room_slug": room.slug,
                "total_value": 10,
                "value": ["0.00"] * len(members),
                "reference_total_value": "0.00",
            },
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert ParentTransaction.objects.get(description="Crafted").room == room
