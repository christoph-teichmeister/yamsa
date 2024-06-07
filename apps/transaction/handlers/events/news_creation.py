from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import (
    ParentTransactionCreated,
)


@message_registry.register_event(event=ParentTransactionCreated)
def create_news_on_parent_transaction_creation(context: ParentTransactionCreated.Context):
    News.objects.create(
        title="New transaction created!",
        message=(
            f"{context.parent_transaction.created_by.name} paid {context.parent_transaction.value} for "
            f"'{context.parent_transaction.description}'"
        ),
        room=context.room,
        created_by=context.parent_transaction.created_by,
    )
