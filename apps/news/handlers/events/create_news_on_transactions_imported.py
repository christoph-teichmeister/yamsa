from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import TransactionsImported


@message_registry.register_event(event=TransactionsImported)
def create_news_on_transactions_imported(context: TransactionsImported.Context):
    room = context.room

    message = _('{importer} imported {count} entries from {source} into "{room}"').format(
        importer=context.triggered_by.name,
        count=context.imported_count + context.settled_count,
        source=context.source_label,
        room=room.name,
    )

    News.objects.create(
        message=message,
        room_id=room.id,
        deeplink=reverse("transaction:list", kwargs={"room_slug": room.slug}),
        type=News.TypeChoices.TRANSACTION_CREATED,
    )
