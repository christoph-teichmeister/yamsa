from apps.core.event_loop.registry import message_registry
from apps.news.models import FeedItem
from apps.transaction.messages.events.transaction import (
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
)


@message_registry.register_event(event=ParentTransactionCreated)
def create_news_on_parent_transaction_creation(context: ParentTransactionCreated.Context):
    text = (
        context.parent_transaction.description[:85] + "..."
        if len(context.parent_transaction.description) > 90
        else context.parent_transaction.description
    )
    FeedItem.objects.create(
        text=text,
        action=FeedItem.ActionChoices.CREATED,
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )


@message_registry.register_event(event=ParentTransactionUpdated)
def create_news_on_parent_transaction_update(context: ParentTransactionUpdated.Context):
    text = (
        context.parent_transaction.description[:75] + "..."
        if len(context.parent_transaction.description) > 80
        else context.parent_transaction.description
    )
    FeedItem.objects.create(
        text=text,
        action=FeedItem.ActionChoices.MODIFIED,
        room=context.room,
        created_by=context.parent_transaction.lastmodified_by,
    )


@message_registry.register_event(event=ParentTransactionDeleted)
def create_news_on_parent_transaction_deleted(context: ParentTransactionDeleted.Context):
    text = (
        context.parent_transaction.description[:75] + "..."
        if len(context.parent_transaction.description) > 80
        else context.parent_transaction.description
    )
    FeedItem.objects.create(
        text=text,
        action=FeedItem.ActionChoices.DELETED,
        room=context.room,
        created_by=context.parent_transaction.lastmodified_by,
    )
