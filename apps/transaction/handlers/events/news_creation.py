from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import (
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
)


@message_registry.register_event(event=ParentTransactionCreated)
def create_news_on_parent_transaction_creation(context: ParentTransactionCreated.Context):
    News.objects.create(
        title=f'paid for "{context.parent_transaction.description}"',
        message=f"-{context.room.name}",
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )


@message_registry.register_event(event=ParentTransactionUpdated)
def create_news_on_parent_transaction_update(context: ParentTransactionUpdated.Context):
    News.objects.create(
        title=f'modified "{context.parent_transaction.description}"',
        message=f"-{context.room.name}",
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )


@message_registry.register_event(event=ParentTransactionDeleted)
def create_news_on_parent_transaction_deleted(context: ParentTransactionDeleted.Context):
    News.objects.create(
        title=f'deleted "{context.parent_transaction.description}"',
        message=f"-{context.room.name}",
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )
