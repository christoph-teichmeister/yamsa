from datetime import timedelta

import pytest
from django.utils import timezone

from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestAnnotateLastActivity:
    def test_room_with_transaction_uses_transaction_timestamp(self, room, user):
        transaction = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        expected_ts = timezone.now() - timedelta(days=1)
        from apps.transaction.models import ParentTransaction

        ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=expected_ts)

        annotated = Room.objects.filter(pk=room.pk).annotate_last_activity().get()
        assert abs((annotated.last_activity - expected_ts).total_seconds()) < 2

    def test_room_without_transactions_falls_back_to_room_lastmodified_at(self):
        room = RoomFactory()
        annotated = Room.objects.filter(pk=room.pk).annotate_last_activity().get()
        assert annotated.last_activity is not None
        assert abs((annotated.last_activity - room.lastmodified_at).total_seconds()) < 2
