import http
from decimal import Decimal
from unittest import mock

import pytest
from django.test import Client

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.news.models import News
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.services.transaction_deletion_service import TransactionDeletionService
from apps.transaction.tests.conftest import delete_url, let_window_pass, restore_url
from apps.webpush.utils import Notification

pytestmark = pytest.mark.django_db

DEBT_FIELDS = ("debitor", "creditor", "value")


class TestRestore:
    def test_the_undo_brings_back_the_transaction_and_its_debts(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        debts_before = list(Debt.objects.filter(room=room, settled=False).values_list(*DEBT_FIELDS))
        assert debts_before
        authenticated_client.post(delete_url(room, shared_expense))

        response = authenticated_client.post(restore_url(room, shared_expense))

        assert response.status_code == http.HTTPStatus.FOUND
        restored = ParentTransaction.objects.get(pk=shared_expense.pk)
        assert restored.deleted_at is None
        assert restored.deleted_by is None
        assert restored.value == Decimal(26)
        assert list(Debt.objects.filter(room=room, settled=False).values_list(*DEBT_FIELDS)) == debts_before

    def test_nobody_is_ever_told_of_an_undone_delete(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        with mock.patch.object(Notification, "send_to_user") as send:
            authenticated_client.post(delete_url(room, shared_expense))
            authenticated_client.post(restore_url(room, shared_expense))
            TransactionDeletionService.finalise_expired()

        send.assert_not_called()
        assert not News.objects.filter(room=room, type=News.TypeChoices.TRANSACTION_DELETED).exists()

    def test_the_undo_is_refused_once_the_window_has_passed(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))
        let_window_pass(shared_expense)

        response = authenticated_client.post(restore_url(room, shared_expense))

        assert response.status_code == http.HTTPStatus.FOUND
        assert not ParentTransaction.objects.filter(pk=shared_expense.pk).exists()
        assert not Debt.objects.filter(room=room, settled=False).exists()

    def test_a_transaction_that_is_not_deleted_is_left_alone(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(restore_url(room, shared_expense))

        assert ParentTransaction.objects.filter(pk=shared_expense.pk).exists()

    def test_a_member_of_another_room_cannot_undo(
        self, client: Client, room: Room, user: User, shared_expense: ParentTransaction
    ) -> None:
        outsider = UserFactory()
        other_room = RoomFactory(created_by=outsider)
        other_room.users.add(outsider)
        TransactionDeletionService.trash(shared_expense, user=user)
        client.force_login(outsider)

        client.post(restore_url(other_room, shared_expense))

        assert not ParentTransaction.objects.filter(pk=shared_expense.pk).exists()

    def test_restore_is_post_only(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        response = authenticated_client.get(restore_url(room, shared_expense))

        assert response.status_code == http.HTTPStatus.METHOD_NOT_ALLOWED
