from datetime import date
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from apps.account.models import User
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


HANDLE_MESSAGE = "apps.debt.views.debt_settle_view.handle_message"


@pytest.fixture
def debt(room: Room, user: User, guest_user: User) -> Debt:
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
    return Debt.objects.get(room=room, settled=False)


def settle_url(debt: Debt) -> str:
    return reverse("debt:settle", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


class TestSettling:
    @freeze_time("2026-03-14 12:00:00")
    def test_the_settlement_date_is_set_by_the_server_not_the_request(
        self, authenticated_client: Client, debt: Debt
    ) -> None:
        authenticated_client.post(settle_url(debt), data={"settled": "true", "settled_at": "2001-01-01"})

        debt.refresh_from_db()
        assert debt.settled_at == date(2026, 3, 14)

    def test_the_notification_goes_out_after_the_debt_is_saved(self, authenticated_client: Client, debt: Debt) -> None:
        settled_when_notified = []

        def record(message: DebtSettled) -> None:
            settled_when_notified.append(Debt.objects.get(pk=message.Context.debt.pk).settled)

        with mock.patch(HANDLE_MESSAGE, side_effect=record) as handle_message:
            authenticated_client.post(settle_url(debt), data={"settled": "true"})

        handle_message.assert_called_once()
        assert settled_when_notified == [True]

    def test_unsettling_notifies_nobody_and_clears_the_date(self, authenticated_client: Client, debt: Debt) -> None:
        Debt.objects.filter(pk=debt.pk).update(settled=True, settled_at=date(2026, 3, 1))

        with mock.patch(HANDLE_MESSAGE) as handle_message:
            authenticated_client.post(settle_url(debt), data={})

        handle_message.assert_not_called()
        debt.refresh_from_db()
        assert debt.settled is False
        assert debt.settled_at is None

    def test_settling_an_already_settled_debt_again_is_silent_and_keeps_its_date(
        self, authenticated_client: Client, debt: Debt
    ) -> None:
        Debt.objects.filter(pk=debt.pk).update(settled=True, settled_at=date(2026, 3, 1))

        with mock.patch(HANDLE_MESSAGE) as handle_message:
            authenticated_client.post(settle_url(debt), data={"settled": "true"})

        handle_message.assert_not_called()
        debt.refresh_from_db()
        assert debt.settled_at == date(2026, 3, 1)

    def test_a_later_optimisation_keeps_the_settled_debt_and_adds_no_duplicate(
        self, authenticated_client: Client, room: Room, debt: Debt
    ) -> None:
        authenticated_client.post(settle_url(debt), data={"settled": "true"})

        DebtOptimiseService.process(room.id)

        assert list(Debt.objects.filter(room=room).values_list("settled", flat=True)) == [True]
