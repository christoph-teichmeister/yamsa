import pytest
from django.db import IntegrityError, transaction

from apps.debt.models import Debt

pytestmark = pytest.mark.django_db


class TestStateMachine:
    def test_marking_as_paid_keeps_the_debt_unsettled(self, debt: Debt) -> None:
        assert debt.mark_as_paid() is True

        debt.refresh_from_db()
        assert (debt.awaiting_confirmation, debt.settled, debt.settled_at) == (True, False, None)

    def test_marking_as_paid_twice_changes_nothing(self, pending_debt: Debt) -> None:
        assert pending_debt.mark_as_paid() is False

    def test_a_settled_debt_cannot_be_marked_as_paid_or_reopened(self, debt: Debt) -> None:
        debt.settle()

        assert debt.mark_as_paid() is False
        assert debt.reopen() is False
        assert debt.settled is True

    def test_settling_a_pending_debt_clears_the_pending_flag(self, pending_debt: Debt) -> None:
        assert pending_debt.settle() is True

        pending_debt.refresh_from_db()
        assert (pending_debt.settled, pending_debt.awaiting_confirmation) == (True, False)
        assert pending_debt.settled_at is not None

    def test_reopening_needs_a_pending_debt(self, debt: Debt, pending_debt: Debt) -> None:
        assert pending_debt.reopen() is True
        assert pending_debt.reopen() is False

    def test_the_database_refuses_settled_and_pending_together(self, debt: Debt) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            Debt.objects.filter(pk=debt.pk).update(settled=True, awaiting_confirmation=True)
