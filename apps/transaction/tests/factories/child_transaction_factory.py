from decimal import Decimal

import factory
from factory import SubFactory

from apps.account.tests.factories import UserFactory
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories.parent_transaction_factory import ParentTransactionFactory


class ChildTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChildTransaction

    parent_transaction = SubFactory(ParentTransactionFactory)
    paid_for = SubFactory(UserFactory)
    value = Decimal("5")
