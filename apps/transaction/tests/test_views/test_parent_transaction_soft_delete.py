import http
from unittest import mock

import pytest
from django.test import Client

from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.debt.models import Debt
from apps.news.models import News
from apps.room.models import Room
from apps.transaction.constants import DELETE_UNDO_SECONDS
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.conftest import delete_url, restore_url
from apps.webpush.utils import Notification

pytestmark = pytest.mark.django_db


class TestSoftDelete:
    def test_the_delete_hides_the_transaction_everywhere(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))

        assert not ParentTransaction.objects.filter(pk=shared_expense.pk).exists()
        assert not room.parent_transactions.filter(pk=shared_expense.pk).exists()
        assert not ChildTransaction.objects.filter(parent_transaction=shared_expense).exists()
        assert ParentTransaction.all_objects.get(pk=shared_expense.pk).deleted_at is not None

    def test_the_debts_are_recalculated_at_once(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        assert Debt.objects.filter(room=room, settled=False).exists()

        authenticated_client.post(delete_url(room, shared_expense))

        assert not Debt.objects.filter(room=room, settled=False).exists()

    def test_nobody_is_told_while_the_undo_is_possible(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        with mock.patch.object(Notification, "send_to_user") as send:
            authenticated_client.post(delete_url(room, shared_expense))

        send.assert_not_called()
        assert not News.objects.filter(room=room, type=News.TypeChoices.TRANSACTION_DELETED).exists()

    def test_the_toast_offers_the_undo_for_ten_seconds(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))

        (toast,) = authenticated_client.session[ToastMiddleware.CARRIED_TOASTS_SESSION_KEY]
        assert toast["action_url"] == restore_url(room, shared_expense)
        assert toast["duration_ms"] == DELETE_UNDO_SECONDS * 1000
        assert toast["action_label"]

    def test_a_deleted_transaction_cannot_be_deleted_again(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))

        response = authenticated_client.post(delete_url(room, shared_expense))

        assert response.status_code == http.HTTPStatus.NOT_FOUND
