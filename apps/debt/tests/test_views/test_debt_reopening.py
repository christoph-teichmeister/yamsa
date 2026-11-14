import http
from datetime import date
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.debt.messages.events.debt_payment_rejected import DebtPaymentRejected
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db

REOPEN_MESSAGES = "apps.debt.views.debt_reopen_view.handle_message"


def reopen_url(debt: Debt) -> str:
    return reverse("debt:reopen", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def login(client: Client, who: User) -> Client:
    client.force_login(who)
    return client


class TestReopening:
    def test_the_creditor_rejects_and_the_debitor_is_told(self, client: Client, pending_debt: Debt, user: User) -> None:
        with mock.patch(REOPEN_MESSAGES) as handle_message:
            response = login(client, user).post(reopen_url(pending_debt))

        assert response.status_code == http.HTTPStatus.FOUND
        pending_debt.refresh_from_db()
        assert (pending_debt.awaiting_confirmation, pending_debt.settled) == (False, False)
        event = handle_message.call_args.args[0]
        assert isinstance(event, DebtPaymentRejected)

    def test_the_debtor_withdraws_silently(self, client: Client, pending_debt: Debt, guest_user: User) -> None:
        with mock.patch(REOPEN_MESSAGES) as handle_message:
            login(client, guest_user).post(reopen_url(pending_debt))

        pending_debt.refresh_from_db()
        assert pending_debt.awaiting_confirmation is False
        handle_message.assert_not_called()

    def test_a_settled_debt_cannot_be_reopened(self, client: Client, debt: Debt, user: User) -> None:
        Debt.objects.filter(pk=debt.pk).update(settled=True, settled_at=date(2026, 3, 1))

        with mock.patch(REOPEN_MESSAGES) as handle_message:
            login(client, user).post(reopen_url(debt))

        handle_message.assert_not_called()
        debt.refresh_from_db()
        assert debt.settled is True

    def test_an_open_debt_rejected_again_is_silent(self, client: Client, debt: Debt, user: User) -> None:
        with mock.patch(REOPEN_MESSAGES) as handle_message:
            login(client, user).post(reopen_url(debt))

        handle_message.assert_not_called()

    def test_a_bystander_is_refused(self, client: Client, room: Room, pending_debt: Debt) -> None:
        bystander = GuestUserFactory()
        room.users.add(bystander)

        response = login(client, bystander).post(reopen_url(pending_debt))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        pending_debt.refresh_from_db()
        assert pending_debt.awaiting_confirmation is True

    def test_an_outsider_is_refused(self, client: Client, pending_debt: Debt) -> None:
        response = login(client, UserFactory()).post(reopen_url(pending_debt))

        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_a_closed_room_refuses(self, client: Client, closed_room: Room, user: User, guest_user: User) -> None:
        create_parent_transaction_with_optimisation(room=closed_room, paid_by=user, paid_for_tuple=(guest_user,))
        closed_debt = Debt.objects.get(room=closed_room, settled=False)
        Debt.objects.filter(pk=closed_debt.pk).update(awaiting_confirmation=True)

        response = login(client, user).post(reopen_url(closed_debt))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        closed_debt.refresh_from_db()
        assert closed_debt.awaiting_confirmation is True

    def test_get_is_not_allowed(self, client: Client, pending_debt: Debt, user: User) -> None:
        response = login(client, user).get(reopen_url(pending_debt))

        assert response.status_code == http.HTTPStatus.METHOD_NOT_ALLOWED
