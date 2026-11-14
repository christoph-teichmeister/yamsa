from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.messages.events.debt_marked_paid import DebtMarkedPaid
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt

pytestmark = pytest.mark.django_db

SETTLE_MESSAGES = "apps.debt.views.debt_settle_view.handle_message"
REOPEN_MESSAGES = "apps.debt.views.debt_reopen_view.handle_message"


def settle_url(debt: Debt) -> str:
    return reverse("debt:settle", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def reopen_url(debt: Debt) -> str:
    return reverse("debt:reopen", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def login(client: Client, who: User) -> Client:
    client.force_login(who)
    return client


class TestMarkingAsPaid:
    def test_the_debtor_marks_it_and_the_creditor_is_told(self, client: Client, debt: Debt, guest_user: User) -> None:
        with mock.patch(SETTLE_MESSAGES) as handle_message:
            login(client, guest_user).post(settle_url(debt), data={"settled": "true"})

        debt.refresh_from_db()
        assert (debt.awaiting_confirmation, debt.settled) == (True, False)
        handle_message.assert_called_once()
        event = handle_message.call_args.args[0]
        assert isinstance(event, DebtMarkedPaid)
        assert event.Context.debt == debt

    def test_a_repeated_post_stays_silent(self, client: Client, pending_debt: Debt, guest_user: User) -> None:
        with mock.patch(SETTLE_MESSAGES) as handle_message:
            login(client, guest_user).post(settle_url(pending_debt), data={"settled": "true"})

        handle_message.assert_not_called()

    def test_the_creditor_confirming_settles_and_tells_the_debitor(
        self, client: Client, pending_debt: Debt, user: User
    ) -> None:
        with mock.patch(SETTLE_MESSAGES) as handle_message:
            login(client, user).post(settle_url(pending_debt), data={"settled": "true"})

        pending_debt.refresh_from_db()
        assert (pending_debt.settled, pending_debt.awaiting_confirmation) == (True, False)
        assert pending_debt.settled_at is not None
        event = handle_message.call_args.args[0]
        assert isinstance(event, DebtSettled)
        assert event.Context.settled_by == user

    def test_a_debtor_cannot_settle_by_posting_again_after_marking(
        self, client: Client, debt: Debt, guest_user: User
    ) -> None:
        login(client, guest_user)
        client.post(settle_url(debt), data={"settled": "true"})
        client.post(settle_url(debt), data={"settled": "true"})

        debt.refresh_from_db()
        assert debt.settled is False
