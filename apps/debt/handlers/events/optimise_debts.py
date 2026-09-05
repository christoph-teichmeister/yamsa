from apps.core.event_loop.registry import message_registry
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.transaction.messages.events.transaction import (
    ChildTransactionDeleted,
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
    TransactionsImported,
)


@message_registry.register_event(event=ParentTransactionCreated)
@message_registry.register_event(event=ParentTransactionUpdated)
@message_registry.register_event(event=ParentTransactionDeleted)
@message_registry.register_event(event=ChildTransactionDeleted)
@message_registry.register_event(event=TransactionsImported)
def calculate_optimised_debts(
    context: ParentTransactionCreated.Context
    | ParentTransactionUpdated.Context
    | ChildTransactionDeleted.Context
    | ParentTransactionDeleted.Context
    | TransactionsImported.Context,
):
    DebtOptimiseService.process(room_id=context.room.id)
