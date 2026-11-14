import pytest

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation


@pytest.fixture
def debitor(room: Room) -> User:
    member = UserFactory()
    room.users.add(member)
    return member


@pytest.fixture
def debt(room: Room, user: User, debitor: User) -> Debt:
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(debitor,))
    return Debt.objects.get(room=room, settled=False)
