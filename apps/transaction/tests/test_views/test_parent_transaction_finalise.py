from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.news.models import News
from apps.room.models import Room
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.services.transaction_deletion_service import TransactionDeletionService
from apps.transaction.tests.conftest import delete_url, let_window_pass
from apps.webpush.utils import Notification

pytestmark = pytest.mark.django_db


class TestFinalise:
    def test_a_delete_still_inside_the_window_is_kept(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))

        assert TransactionDeletionService.finalise_expired() == 0
        assert ParentTransaction.all_objects.filter(pk=shared_expense.pk).exists()

    def test_an_expired_delete_is_final_and_tells_the_room_once(
        self, authenticated_client: Client, room: Room, guest_user: User, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))
        let_window_pass(shared_expense)

        with mock.patch.object(Notification, "send_to_user") as send:
            assert TransactionDeletionService.finalise_expired() == 1
            notified_after_first_run = send.call_count
            assert TransactionDeletionService.finalise_expired() == 0

        assert not ParentTransaction.all_objects.filter(pk=shared_expense.pk).exists()
        assert not ChildTransaction.all_objects.filter(parent_transaction_id=shared_expense.pk).exists()
        assert News.objects.filter(room=room, type=News.TypeChoices.TRANSACTION_DELETED).count() == 1
        assert "26" in News.objects.get(room=room, type=News.TypeChoices.TRANSACTION_DELETED).message
        assert guest_user in [call.args[0] for call in send.call_args_list]
        assert send.call_count == notified_after_first_run

    def test_visiting_the_list_finalises_the_rooms_expired_deletes(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))
        let_window_pass(shared_expense)

        authenticated_client.get(reverse("transaction:list", kwargs={"room_slug": room.slug}))

        assert not ParentTransaction.all_objects.filter(pk=shared_expense.pk).exists()

    def test_the_command_finalises_every_room(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))
        let_window_pass(shared_expense)
        out = StringIO()

        call_command("purge_deleted_transactions", stdout=out)

        assert "Deleted 1" in out.getvalue()
        assert not ParentTransaction.all_objects.filter(pk=shared_expense.pk).exists()
