from apps.core.event_loop.registry import message_registry
from apps.transaction.messages.commands.transaction import CreateTransaction
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_command(command=CreateTransaction)
def handle_create_transaction(context: CreateTransaction.Context) -> TransactionCreated:
    return TransactionCreated(
        context_data={
            "room": context.room,
            "value": context.value,
            "creditor": context.creditor,
            "debitor": context.debitor,
        }
    )
