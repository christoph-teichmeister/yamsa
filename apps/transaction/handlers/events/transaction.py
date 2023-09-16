from apps.core.domain import message_registry
from apps.moneyflow.models import MoneyFlow
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_event(event=TransactionCreated)
def handle_transaction_created(context: TransactionCreated.Context):
    MoneyFlow.objects.create_or_update_flows_for_transaction(transaction=context.transaction)
