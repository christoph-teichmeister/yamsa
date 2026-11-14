import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import delete_url

pytestmark = pytest.mark.django_db


class TestEveryReaderSkipsADeletedTransaction:
    def test_list_export_money_spent_and_detail(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))
        kwargs = {"room_slug": room.slug}

        listing = authenticated_client.get(reverse("transaction:list", kwargs=kwargs))
        export = authenticated_client.get(reverse("transaction:export", kwargs=kwargs))
        money_spent = authenticated_client.get(reverse("debt:money-spent-on-room", kwargs=kwargs))
        detail = authenticated_client.get(reverse("transaction:detail", kwargs={**kwargs, "pk": shared_expense.pk}))

        assert listing.context_data["transactions_total_count"] == 0
        assert shared_expense.description not in b"".join(export.streaming_content).decode()
        assert not money_spent.context_data["total_money_spent"]
        assert detail.status_code == http.HTTPStatus.NOT_FOUND

    def test_a_room_with_only_a_deleted_transaction_has_no_last_activity_from_it(
        self, authenticated_client: Client, room: Room, shared_expense: ParentTransaction
    ) -> None:
        authenticated_client.post(delete_url(room, shared_expense))

        annotated = Room.objects.annotate_last_activity().get(pk=room.pk)

        assert annotated.last_transaction_at is None
