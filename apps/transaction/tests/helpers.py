from typing import Tuple

from _decimal import Decimal
from django.urls import reverse

from apps.account.models import User
from apps.core.http_status import HttpStatus
from apps.room.models import Room


class TransactionHelpersMixin:
    def create_transaction(
        self,
        *,
        paid_for: Tuple[int, ...],
        paid_by: User,
        room: Room,
        value: Decimal,
    ):
        description = (
            f"{paid_by.name} {Decimal(value)}{room.preferred_currency.sign} for "
            f"{', '.join([str(e for e in paid_for)])}"
        )
        response = self.client.post(
            reverse("transaction-add"),
            data={
                "description": description,
                "paid_for": paid_for,
                "paid_by": paid_by.id,
                "room": room.id,
                "currency": room.preferred_currency_id,
                "room_slug": room.slug,
                "value": value,
            },
        )
        self.assertEqual(response.status_code, HttpStatus.HTTP_302_FOUND)

        created_transaction_qs = paid_by.made_transactions.filter(
            room_id=room.id,
            value=round(value / len(paid_for), 2),
            paid_for__id__in=paid_for,
        )
        self.assertTrue(
            created_transaction_qs.count() > 0, [e for e in created_transaction_qs]
        )

        return created_transaction_qs.first()
