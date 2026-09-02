from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.transaction.messages.events.transaction import ParentTransactionCreated


@message_registry.register_event(event=ParentTransactionCreated)
def create_news_on_transaction_create(context: ParentTransactionCreated.Context):
    parent_transaction = context.parent_transaction

    if not parent_transaction.created_by or parent_transaction.created_by == parent_transaction.paid_by:
        message = _('{payer} logged a payment of {amount}{currency} in "{room}"').format(
            payer=parent_transaction.paid_by.name,
            amount=parent_transaction.value,
            currency=parent_transaction.currency.sign,
            room=parent_transaction.room.name,
        )
    else:
        message = _('{creator} logged that {payer} paid {amount}{currency} in "{room}"').format(
            creator=parent_transaction.created_by.name,
            payer=parent_transaction.paid_by.name,
            amount=parent_transaction.value,
            currency=parent_transaction.currency.sign,
            room=parent_transaction.room.name,
        )

    deeplink = reverse(
        "transaction:detail",
        kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.pk},
    )

    News.objects.create(
        message=message,
        room_id=parent_transaction.room_id,
        deeplink=deeplink,
        type=News.TypeChoices.TRANSACTION_CREATED,
    )
