from apps.core.domain import message_registry
from apps.transaction.messages.commands.transaction import CreateTransaction
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_command(command=CreateTransaction)
def handle_create_transaction(context: CreateTransaction.Context) -> TransactionCreated:
    # Transaction.objects.create_transaction(
    #     faction=context.faction, amount=-amount, reason=f"Salaries of {amount} silver paid in week {context.week}."
    # )

    return TransactionCreated(
        context_data={
            "room": context.room,
            "value": context.value,
            "creditor": context.creditor,
            "debitor": context.debitor,
        }
    )
