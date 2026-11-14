import http
from datetime import UTC, datetime

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.room.models import Room
from apps.transaction.models import Category, ParentTransaction

pytestmark = pytest.mark.django_db


class TestTransactionCreateRejectsForeignPayer:
    def _post(self, client: Client, room: Room, *, paid_by: int, paid_for: list[int]) -> object:
        return client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "category": Category.objects.get(slug="groceries").id,
                "description": "Crafted",
                "currency": room.preferred_currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": paid_by,
                "paid_for": [str(pk) for pk in paid_for],
                "room_slug": room.slug,
                "total_value": 10,
                "value": ["0.00"] * len(paid_for),
                "reference_total_value": "0.00",
            },
        )

    def test_a_payer_outside_the_room_is_refused(self, authenticated_client: Client, room: Room) -> None:
        member_ids = [m.id for m in room.users.all()]

        response = self._post(authenticated_client, room, paid_by=UserFactory().id, paid_for=member_ids)

        assert response.status_code == http.HTTPStatus.OK
        assert not ParentTransaction.objects.filter(description="Crafted").exists()

    def test_split_rows_survive_a_validation_error(self, authenticated_client: Client, room: Room) -> None:
        member_ids = [m.id for m in room.users.all()]

        response = self._post(authenticated_client, room, paid_by=UserFactory().id, paid_for=member_ids)

        assert [row["paid_for_id"] for row in response.context["split_rows"]] == [str(pk) for pk in member_ids]
