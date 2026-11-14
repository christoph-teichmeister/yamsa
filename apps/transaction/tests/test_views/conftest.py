import pytest

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation


@pytest.fixture
def shared_expense(room: Room, user: User, guest_user: User) -> ParentTransaction:
    """An expense of 26 split 13/13 between the payer and the guest, with its debt calculated."""
    parent, _ = create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(user, guest_user))
    return parent
