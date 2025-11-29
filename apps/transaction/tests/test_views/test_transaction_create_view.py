import http
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker

from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views import TransactionListView

pytestmark = pytest.mark.django_db


class TestTransactionCreateView:
    @freeze_time("2020-04-04 4:20:00")
    def test_post_regular(self, authenticated_client, room, user):
        assert room.users.count() > 1, "This test requires more than one participant in the room"

        currency = baker.make_recipe("apps.currency.tests.currency")
        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "description": "My description",
                "currency": currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": user.id,
                "room": room.id,
                "paid_for": [str(member.id) for member in room.users.all()],
                "room_slug": room.slug,
                "value": 10,
            },
            follow=True,
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == TransactionListView.template_name
        assert "Room transactions" in response.content.decode()
        assert response.context_data["active_tab"] == "transaction"

        assert ParentTransaction.objects.filter(description="My description", room=room, paid_by=user).exists()

        child_transaction_value = Decimal("10") / room.users.count()
        for member in room.users.all():
            qs = ChildTransaction.objects.filter(paid_for=member, value=child_transaction_value)
            assert qs.exists()
