from collections.abc import Callable
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory


@pytest.mark.e2e
class TestDebtUnsettle:
    def test_settling_stamps_the_server_date_and_unsettling_clears_it(
        self, debt_list_as: Callable, roommate: User, open_debt: Debt, room_with_open_debt: Room
    ) -> None:
        debt_list_page = debt_list_as(roommate)

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.confirm_settlement()
        debt_list_page.expect_settled(open_debt.id)

        open_debt.refresh_from_db()
        assert open_debt.settled_at == timezone.localdate()

        settle_path = reverse("debt:settle", kwargs={"room_slug": room_with_open_debt.slug, "pk": open_debt.id})
        # A date riding along with the un-settling must not survive it either.
        response = debt_list_page.post(settle_path, {"settled_at": "2001-01-01"})

        assert response.status == HTTPStatus.FOUND
        open_debt.refresh_from_db()
        assert open_debt.settled is False
        assert open_debt.settled_at is None
        debt_list_page.navigate()
        debt_list_page.expect_open_for_debtor(open_debt.id)

    def test_a_date_sent_with_the_request_is_ignored(
        self, debt_list_as: Callable, roommate: User, open_debt: Debt, room_with_open_debt: Room
    ) -> None:
        debt_list_page = debt_list_as(roommate)
        settle_path = reverse("debt:settle", kwargs={"room_slug": room_with_open_debt.slug, "pk": open_debt.id})

        debt_list_page.post(settle_path, {"settled": "true", "settled_at": "2001-01-01"})

        open_debt.refresh_from_db()
        assert open_debt.settled is True
        assert open_debt.settled_at == timezone.localdate()

    def test_a_debt_of_another_room_cannot_be_settled_through_this_room(
        self, debt_list_as: Callable, roommate: User, profile_user: User, room_with_open_debt: Room
    ) -> None:
        other_room = RoomFactory(created_by=profile_user)
        other_room.users.add(profile_user, roommate)
        foreign_debt = Debt.objects.create(
            room=other_room,
            debitor=roommate,
            creditor=profile_user,
            value=Decimal("7.00"),
            currency=other_room.preferred_currency,
        )
        connection.close()
        debt_list_page = debt_list_as(roommate)

        response = debt_list_page.post(
            reverse("debt:settle", kwargs={"room_slug": room_with_open_debt.slug, "pk": foreign_debt.id}),
            {"settled": "true"},
        )

        assert response.status == HTTPStatus.NOT_FOUND
        foreign_debt.refresh_from_db()
        assert foreign_debt.settled is False
