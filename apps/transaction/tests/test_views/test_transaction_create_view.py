import http
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from freezegun import freeze_time

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views import TransactionListView

pytestmark = pytest.mark.django_db


class TestTransactionCreateView:
    @freeze_time("2020-04-04 4:20:00")
    def test_post_regular(self, authenticated_client, room, user):
        assert room.users.count() > 1, "This test requires more than one participant in the room"

        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "description": "My description",
                "currency": room.preferred_currency.id,
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
        parent_transaction = ParentTransaction.objects.get(description="My description", room=room, paid_by=user)
        assert parent_transaction.value == Decimal("10")

        child_transaction_value = Decimal("10") / room.users.count()
        for member in room.users.all():
            qs = ChildTransaction.objects.filter(paid_for=member, value=child_transaction_value)
            assert qs.exists()

    def test_form_valid_fires_handle_message_outside_atomic(self):
        """
        Regression test for #333: handle_message must be called from form_valid,
        not from inside form.save() (which runs inside transaction.atomic).
        Calling it from within the atomic block held the DB connection open
        during webpush HTTP requests, blocking consecutive saves.
        """
        from unittest.mock import MagicMock

        from django.utils import timezone

        from apps.transaction.views.transaction_create_view import TransactionCreateView

        user = UserFactory()
        other_user = UserFactory()
        room = RoomFactory(created_by=user)
        room.users.add(user, other_user)
        currency = CurrencyFactory()

        view = TransactionCreateView()
        view.request = MagicMock(user=user, room=room, method="POST")
        view.kwargs = {"room_slug": room.slug}
        view.object = None

        form = TransactionCreateForm(
            data={
                "description": "Test",
                "currency": currency.id,
                "paid_at": timezone.now(),
                "paid_by": user.id,
                "room": room.id,
                "paid_for": [user.id, other_user.id],
                "room_slug": room.slug,
                "value": "10.00",
            },
            request=MagicMock(user=user),
            room=room,
        )
        assert form.is_valid(), form.errors

        with patch("apps.transaction.views.transaction_create_view.handle_message") as mock_handle:
            view.form_valid(form)

        mock_handle.assert_called_once()
