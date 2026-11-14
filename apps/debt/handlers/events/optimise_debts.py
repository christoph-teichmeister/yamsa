from apps.core.event_loop.registry import message_registry
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.transaction.messages.events.transaction import (
    ChildTransactionDeleted,
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionRestored,
    ParentTransactionTrashed,
    ParentTransactionUpdated,
    TransactionsImported,
)


@message_registry.register_event(event=ParentTransactionCreated)
@message_registry.register_event(event=ParentTransactionUpdated)
@message_registry.register_event(event=ParentTransactionDeleted)
@message_registry.register_event(event=ParentTransactionTrashed)
@message_registry.register_event(event=ParentTransactionRestored)
@message_registry.register_event(event=ChildTransactionDeleted)
@message_registry.register_event(event=TransactionsImported)
def calculate_optimised_debts(
    context: ParentTransactionCreated.Context
    | ParentTransactionUpdated.Context
    | ChildTransactionDeleted.Context
    | ParentTransactionDeleted.Context
    | ParentTransactionTrashed.Context
    | ParentTransactionRestored.Context
    | TransactionsImported.Context,
) -> None:
    DebtOptimiseService.process(room_id=context.room.id)
