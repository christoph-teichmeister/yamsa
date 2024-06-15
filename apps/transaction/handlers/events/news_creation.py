from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import (
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
)


@message_registry.register_event(event=ParentTransactionCreated)
def create_news_on_parent_transaction_creation(context: ParentTransactionCreated.Context):
    description = (
        context.parent_transaction.description[:85] + "..."
        if len(context.parent_transaction.description) > 90
        else context.parent_transaction.description
    )
    News.objects.create(
        title=f'"{description}" created',
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )


@message_registry.register_event(event=ParentTransactionUpdated)
def create_news_on_parent_transaction_update(context: ParentTransactionUpdated.Context):
    description = (
        context.parent_transaction.description[:75] + "..."
        if len(context.parent_transaction.description) > 80
        else context.parent_transaction.description
    )
    News.objects.create(
        title=f'"{description}" was modified',
        room=context.room,
        created_by=context.parent_transaction.lastmodified_by,
    )


@message_registry.register_event(event=ParentTransactionDeleted)
def create_news_on_parent_transaction_deleted(context: ParentTransactionDeleted.Context):
    description = (
        context.parent_transaction.description[:75] + "..."
        if len(context.parent_transaction.description) > 80
        else context.parent_transaction.description
    )
    News.objects.create(
        title=f'"{description}" was deleted',
        room=context.room,
        created_by=context.parent_transaction.lastmodified_by,
    )
