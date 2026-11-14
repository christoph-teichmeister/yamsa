import http
from unittest import mock

import pytest
from django.test import Client

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt, ReminderLog
from apps.debt.tests.test_views.remind_helpers import PUSH, remind_url
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestWhoMayRemind:
    def test_the_debitor_is_refused(self, client: Client, debitor: User, debt: Debt) -> None:
        client.force_login(debitor)

        response = client.post(remind_url(debt))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert not ReminderLog.objects.exists()

    def test_another_member_is_refused(self, client: Client, room: Room, debt: Debt) -> None:
        bystander = UserFactory()
        room.users.add(bystander)
        client.force_login(bystander)

        assert client.post(remind_url(debt)).status_code == http.HTTPStatus.FORBIDDEN

    def test_an_outsider_is_refused(self, client: Client, debt: Debt) -> None:
        client.force_login(UserFactory())

        assert client.post(remind_url(debt)).status_code == http.HTTPStatus.FORBIDDEN

    def test_a_settled_debt_is_refused(self, client: Client, user: User, debt: Debt) -> None:
        Debt.objects.filter(pk=debt.pk).update(settled=True)
        client.force_login(user)

        with mock.patch(PUSH) as push:
            response = client.post(remind_url(debt))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        push.assert_not_called()

    def test_a_guest_debitor_is_refused(self, client: Client, room: Room, user: User, guest_user: User) -> None:
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        guest_debt = Debt.objects.get(room=room, settled=False)
        client.force_login(user)

        assert client.post(remind_url(guest_debt)).status_code == http.HTTPStatus.FORBIDDEN

    def test_a_closed_room_is_refused(self, client: Client, user: User, debt: Debt) -> None:
        Room.objects.filter(pk=debt.room_id).update(status=Room.StatusChoices.CLOSED)
        client.force_login(user)

        assert client.post(remind_url(debt)).status_code == http.HTTPStatus.FORBIDDEN

    def test_get_is_not_allowed(self, client: Client, user: User, debt: Debt) -> None:
        client.force_login(user)

        assert client.get(remind_url(debt)).status_code == http.HTTPStatus.METHOD_NOT_ALLOWED
