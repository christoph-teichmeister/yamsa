from datetime import timedelta

import pytest
from django.utils import timezone

from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestRoomQsForListOrdering:
    def test_rooms_ordered_by_most_recent_activity_first(self, user):
        now = timezone.now()

        old_room = RoomFactory(created_by=user)
        old_room.users.add(user)
        new_room = RoomFactory(created_by=user)
        new_room.users.add(user)

        old_tx = ParentTransactionFactory(room=old_room, paid_by=user, currency=old_room.preferred_currency)
        ParentTransaction.objects.filter(pk=old_tx.pk).update(lastmodified_at=now - timedelta(days=10))

        new_tx = ParentTransactionFactory(room=new_room, paid_by=user, currency=new_room.preferred_currency)
        ParentTransaction.objects.filter(pk=new_tx.pk).update(lastmodified_at=now - timedelta(days=1))

        if "room_qs_for_list" in user.__dict__:
            del user.__dict__["room_qs_for_list"]

        slugs = [
            str(r["slug"])
            for r in user.room_qs_for_list
            if str(r["slug"]) in {str(old_room.slug), str(new_room.slug)}
        ]

        assert slugs.index(str(new_room.slug)) < slugs.index(str(old_room.slug)), (
            "new_room (more recent activity) should appear before old_room in the side nav"
        )

    def test_room_without_transactions_sorts_after_room_with_transactions(self, user):
        now = timezone.now()

        no_tx_room = RoomFactory(created_by=user)
        no_tx_room.users.add(user)

        tx_room = RoomFactory(created_by=user)
        tx_room.users.add(user)
        tx = ParentTransactionFactory(room=tx_room, paid_by=user, currency=tx_room.preferred_currency)
        ParentTransaction.objects.filter(pk=tx.pk).update(lastmodified_at=now - timedelta(days=1))

        Room.objects.filter(pk=no_tx_room.pk).update(lastmodified_at=now - timedelta(days=30))

        if "room_qs_for_list" in user.__dict__:
            del user.__dict__["room_qs_for_list"]

        slugs = [
            str(r["slug"])
            for r in user.room_qs_for_list
            if str(r["slug"]) in {str(no_tx_room.slug), str(tx_room.slug)}
        ]

        assert slugs.index(str(tx_room.slug)) < slugs.index(str(no_tx_room.slug)), (
            "room with recent transaction should appear before room with no transactions"
        )
