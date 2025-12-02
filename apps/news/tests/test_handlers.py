import pytest
from django.urls import reverse

from apps.news.handlers.events.create_news_on_transaction_create import create_news_on_transaction_create
from apps.news.models import News
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestCreateNewsOnTransactionCreate:
    def test_handler_creates_news_entry_with_expected_payload(self):
        parent_transaction = ParentTransactionFactory()

        context = ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=parent_transaction.room)

        create_news_on_transaction_create(context)

        news = News.objects.get(room=parent_transaction.room, type=News.TypeChoices.TRANSACTION_CREATED)

        expected_message = (
            f"{parent_transaction.paid_by.name} paid "
            f'{parent_transaction.value}{parent_transaction.currency.sign} in "{parent_transaction.room.name}"'
        )
        assert news.message == expected_message

        expected_deeplink = reverse(
            "transaction:detail",
            kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.pk},
        )
        assert news.deeplink == expected_deeplink
