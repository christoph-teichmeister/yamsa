import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


@pytest.fixture
def debt(room: Room, user: User, guest_user: User) -> Debt:
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
    return Debt.objects.get(room=room, settled=False)


def settle_url(debt: Debt) -> str:
    return reverse("debt:settle", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


class TestWhoMayOpenTheSettlement:
    def test_an_outsider_is_refused(self, client: Client, debt: Debt) -> None:
        client.force_login(UserFactory())

        response = client.post(settle_url(debt), data={"settled": "true"})

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        debt.refresh_from_db()
        assert debt.settled is False

    def test_an_anonymous_visitor_is_sent_to_the_login(self, client: Client, debt: Debt) -> None:
        response = client.post(settle_url(debt), data={"settled": "true"})

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url.startswith("/account/login/")
        debt.refresh_from_db()
        assert debt.settled is False

    @pytest.mark.parametrize("member", ["debtor", "creditor", "another_guest"])
    def test_every_member_of_the_room_can_settle(
        self, client: Client, room: Room, debt: Debt, user: User, guest_user: User, member: str
    ) -> None:
        other_guest = GuestUserFactory()
        room.users.add(other_guest)
        client.force_login({"debtor": guest_user, "creditor": user, "another_guest": other_guest}[member])

        response = client.post(settle_url(debt), data={"settled": "true"})

        assert response.status_code == http.HTTPStatus.FOUND
        debt.refresh_from_db()
        assert debt.settled is True

    def test_a_closed_room_refuses_the_settlement(
        self, authenticated_client: Client, closed_room: Room, user: User, guest_user: User
    ) -> None:
        create_parent_transaction_with_optimisation(room=closed_room, paid_by=user, paid_for_tuple=(guest_user,))
        closed_debt = Debt.objects.get(room=closed_room, settled=False)

        response = authenticated_client.post(settle_url(closed_debt), data={"settled": "true"})

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        closed_debt.refresh_from_db()
        assert closed_debt.settled is False
