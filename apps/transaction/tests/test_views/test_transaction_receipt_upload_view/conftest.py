from decimal import Decimal

import pytest

from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.fixture(autouse=True)
def enforce_media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def transaction_with_children(room, user):
    parent_transaction = ParentTransactionFactory(
        room=room,
        paid_by=user,
        currency=room.preferred_currency,
    )

    for member in room.users.all():
        ChildTransaction.objects.create(
            parent_transaction=parent_transaction,
            paid_for=member,
            value=Decimal("5"),
        )

    return parent_transaction
