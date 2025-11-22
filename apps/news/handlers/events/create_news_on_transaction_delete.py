from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import ParentTransactionDeleted


@message_registry.register_event(event=ParentTransactionDeleted)
def create_news_on_transaction_deleted(context: ParentTransactionDeleted.Context):
    parent_transaction = context.parent_transaction

    message = (
        f'{context.user_who_deleted.name} deleted the transaction "{parent_transaction.description}" '
        f'({parent_transaction.value}{parent_transaction.currency.sign}) in "{parent_transaction.room.name}"'
    )

    News.objects.create(
        title=f"🗑️ {parent_transaction.room.capitalised_initials}: Transaction deleted",
        message=message,
        room_id=parent_transaction.room_id,
        type=News.TypeChoices.TRANSACTION_DELETED,
    )
