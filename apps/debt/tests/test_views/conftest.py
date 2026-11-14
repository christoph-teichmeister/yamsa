import pytest

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation


@pytest.fixture
def debt(room: Room, user: User, guest_user: User) -> Debt:
    """``user`` is the creditor, ``guest_user`` the debitor."""
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
    return Debt.objects.get(room=room, settled=False)


@pytest.fixture
def pending_debt(debt: Debt) -> Debt:
    Debt.objects.filter(pk=debt.pk).update(awaiting_confirmation=True)
    debt.refresh_from_db()
    return debt
