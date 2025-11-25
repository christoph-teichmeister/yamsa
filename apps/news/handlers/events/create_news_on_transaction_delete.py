from django.utils.translation import gettext as _

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import ParentTransactionDeleted


@message_registry.register_event(event=ParentTransactionDeleted)
def create_news_on_transaction_deleted(context: ParentTransactionDeleted.Context):
    parent_transaction = context.parent_transaction

    message = _('{actor} deleted the transaction "{description}" ({amount}{currency}) in "{room}"').format(
        actor=context.user_who_deleted.name,
        description=parent_transaction.description,
        amount=parent_transaction.value,
        currency=parent_transaction.currency.sign,
        room=parent_transaction.room.name,
    )

    News.objects.create(
        title=_("{icon} {initials}: Transaction deleted").format(
            icon="🗑️",
            initials=parent_transaction.room.capitalised_initials,
        ),
        message=message,
        room_id=parent_transaction.room_id,
        type=News.TypeChoices.TRANSACTION_DELETED,
    )
