from datetime import timedelta

import pytest
from django.utils import timezone

from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestAnnotateLastActivity:
    def test_room_with_transaction_uses_the_newest_paid_at(self, room, user):
        expected_ts = timezone.now() - timedelta(days=1)
        ParentTransactionFactory(
            room=room, paid_by=user, currency=room.preferred_currency, paid_at=timezone.now() - timedelta(days=9)
        )
        ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency, paid_at=expected_ts)

        annotated = Room.objects.filter(pk=room.pk).annotate_last_activity().get()

        assert annotated.last_activity == expected_ts
        assert annotated.last_transaction_at == expected_ts

    def test_editing_a_transaction_does_not_count_as_activity(self, room, user):
        paid_at = timezone.now() - timedelta(days=365)
        transaction = ParentTransactionFactory(
            room=room, paid_by=user, currency=room.preferred_currency, paid_at=paid_at
        )
        ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=timezone.now())

        annotated = Room.objects.filter(pk=room.pk).annotate_last_activity().get()

        assert annotated.last_activity == paid_at

    def test_room_without_transactions_falls_back_to_room_lastmodified_at(self):
        room = RoomFactory()

        annotated = Room.objects.filter(pk=room.pk).annotate_last_activity().get()

        assert annotated.last_transaction_at is None
        assert abs((annotated.last_activity - room.lastmodified_at).total_seconds()) < 2
