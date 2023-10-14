from apps.core.event_loop.registry import message_registry
from apps.transaction.messages.commands.transaction import CreateParentTransaction
from apps.transaction.messages.events.transaction import ParentTransactionCreated


@message_registry.register_command(command=CreateParentTransaction)
def handle_create_parent_transaction(context: CreateParentTransaction.Context) -> ParentTransactionCreated:
    return ParentTransactionCreated(
        context_data={
            "room": context.room,
            "value": context.value,
            "creditor": context.creditor,
            "debitor": context.debitor,
        }
    )
