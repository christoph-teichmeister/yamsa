"""
Regression test for #333.

The `TransactionCreateForm.save()` wraps everything in `@transaction.atomic`.
Previously, `handle_message(ParentTransactionCreated(...))` was called *inside*
that atomic block, which meant the webpush HTTP request (an external network call)
would hold the DB connection open.  On a slow push service this caused the second
consecutive transaction to block (SQLite) or see a broken connection, resulting in
an error on the first attempt and success on the retry.

Fix: defer `handle_message` via `transaction.on_commit(...)` so all post-commit
side-effects fire only *after* the DB transaction is committed.
"""

from unittest.mock import MagicMock, patch

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import ParentTransaction

pytestmark = pytest.mark.django_db


class TestTransactionCreateFormOnCommit:
    """handle_message must be deferred to on_commit, not called inside the atomic block."""

    def _build_form_data(self, room, user, currency, paid_for_users, description="Test transaction"):
        from django.utils import timezone

        return {
            "description": description,
            "currency": currency.id,
            "paid_at": timezone.now(),
            "paid_by": user.id,
            "room": room.id,
            "paid_for": [u.id for u in paid_for_users],
            "room_slug": room.slug,
            "value": "12.00",
        }

    def test_handle_message_is_deferred_via_on_commit(self):
        """
        handle_message must NOT be called directly inside the @transaction.atomic block —
        it must be wrapped in transaction.on_commit().

        If it were called directly, any slow side-effect (e.g. webpush HTTP call)
        would hold the DB connection open, causing the second consecutive transaction
        to block or fail (regression of issue #333).

        We verify this by intercepting transaction.on_commit and confirming it is
        called exactly once by form.save(), without handle_message being called
        directly in the same stack frame.
        """
        user = UserFactory()
        other_user = UserFactory()
        room = RoomFactory(created_by=user)
        room.users.add(user, other_user)
        currency = CurrencyFactory()

        on_commit_call_count = []

        def spy_on_commit(func, *args, **kwargs):
            on_commit_call_count.append(func)
            # Do NOT delegate to real on_commit — we just want to assert it's registered

        form_data = self._build_form_data(room, user, currency, [user, other_user])
        form = TransactionCreateForm(data=form_data, request=MagicMock(user=user), room=room)
        assert form.is_valid(), form.errors

        on_commit_path = "apps.transaction.forms.transaction_create_form.transaction.on_commit"
        handle_message_path = "apps.transaction.forms.transaction_create_form.handle_message"
        with (
            patch(on_commit_path, side_effect=spy_on_commit) as mock_on_commit,
            patch(handle_message_path) as mock_handle,
        ):
            form.save()

        # handle_message must NOT have been called directly inside save()
        mock_handle.assert_not_called()

        # on_commit must have been called with our deferred lambda
        mock_on_commit.assert_called_once()

    def test_second_consecutive_save_succeeds(self):
        """
        Two consecutive saves in the same process must both persist without error.
        Previously the second would fail because the DB connection was blocked by
        a webpush HTTP call inside the open atomic block (issue #333).
        """
        user = UserFactory()
        other_user = UserFactory()
        room = RoomFactory(created_by=user)
        room.users.add(user, other_user)
        currency = CurrencyFactory()

        request_mock = MagicMock(user=user)

        for i in range(2):
            form_data = self._build_form_data(
                room, user, currency, [user, other_user], description=f"Transaction {i}"
            )
            form = TransactionCreateForm(data=form_data, request=request_mock, room=room)
            assert form.is_valid(), f"Form {i} invalid: {form.errors}"
            form.save()

        assert ParentTransaction.objects.filter(room=room).count() == 2, (
            "Both transactions should be saved — if only 1 exists, "
            "the second save failed (regression of issue #333)."
        )
