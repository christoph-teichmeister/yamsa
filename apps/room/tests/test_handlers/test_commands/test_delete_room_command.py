from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.account.models import User
from apps.debt.models import Debt
from apps.news.models import News
from apps.room.handlers.commands.delete_room import handle_delete_room
from apps.room.messages.commands.delete_room import DeleteRoom
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted
from apps.room.models import Room, UserConnectionToRoom
from apps.transaction.models import ChildTransaction, ParentTransaction, Receipt, RoomCategory
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def create_receipt(parent_transaction, uploaded_by) -> Receipt:
    receipt_file = SimpleUploadedFile("receipt.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
    return Receipt.objects.create(
        parent_transaction=parent_transaction,
        file=receipt_file,
        original_name="receipt.pdf",
        content_type="application/pdf",
        size=receipt_file.size,
        uploaded_by=uploaded_by,
    )


class TestHandleDeleteRoom:
    def test_deleting_a_room_cascades_its_own_data_but_keeps_users(self, room, user, guest_user):
        parent_transaction = ParentTransactionFactory(room=room, paid_by=user)
        ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=guest_user, value=Decimal("5"))
        create_receipt(parent_transaction=parent_transaction, uploaded_by=user)
        Debt.objects.create(
            room=room,
            debitor=guest_user,
            creditor=user,
            value=Decimal("5"),
            currency=room.preferred_currency,
        )
        RoomCategory.objects.create(room=room, category=parent_transaction.category)
        News.objects.create(room=room, message="Something happened")

        result = handle_delete_room(
            DeleteRoom.Context(room=room, user_requesting_deletion=user),
        )

        assert isinstance(result, RoomHardDeleted)
        assert not Room.objects.filter(id=room.id).exists()
        assert not ParentTransaction.objects.filter(room_id=room.id).exists()
        assert not ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id).exists()
        assert not Receipt.objects.filter(parent_transaction_id=parent_transaction.id).exists()
        assert not Debt.objects.filter(room_id=room.id).exists()
        assert not RoomCategory.objects.filter(room_id=room.id).exists()
        assert not News.objects.filter(room_id=room.id).exists()
        assert not UserConnectionToRoom.objects.filter(room_id=room.id).exists()

        assert User.objects.filter(id=user.id).exists()
        assert User.objects.filter(id=guest_user.id).exists()

    def test_the_event_carries_the_recipients_and_receipts_captured_before_the_delete(self, room, user, guest_user):
        parent_transaction = ParentTransactionFactory(room=room, paid_by=user)
        receipt = create_receipt(parent_transaction=parent_transaction, uploaded_by=user)
        receipt_name = receipt.file.name

        result = handle_delete_room(
            DeleteRoom.Context(room=room, user_requesting_deletion=user),
        )

        assert result.Context.room_name == room.name
        assert result.Context.actor_name == user.name
        assert result.Context.member_user_ids == [guest_user.id]
        assert result.Context.receipt_storage_refs == [(receipt.file.storage, receipt_name)]

    def test_the_actor_is_not_among_the_notified_members(self, room, user, guest_user):
        result = handle_delete_room(
            DeleteRoom.Context(room=room, user_requesting_deletion=user),
        )

        assert user.id not in result.Context.member_user_ids
