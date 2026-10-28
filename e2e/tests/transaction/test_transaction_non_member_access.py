from http import HTTPStatus

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.conftest import _login


@pytest.fixture
def booked_room(room: Room, profile_user: User, roommate: User) -> tuple[Room, int, int]:
    parent_transaction = ParentTransactionFactory(room=room, paid_by=profile_user, currency=room.preferred_currency)
    ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=roommate, value="12.00")
    DebtOptimiseService.process(room_id=room.id)
    debt = Debt.objects.get(room=room)
    connection.close()
    return room, parent_transaction.id, debt.id


@pytest.mark.e2e
class TestTransactionNonMemberAccess:
    @pytest.mark.parametrize(
        "url_name",
        [
            "transaction:list",
            "transaction:create",
            "transaction:detail",
            "transaction:edit",
            "debt:list",
            "debt:settle",
        ],
    )
    def test_a_user_outside_the_room_cannot_open_its_pages(
        self,
        page: Page,
        base_url: str,
        booked_room: tuple[Room, int, int],
        unrelated_user: User,
        url_name: str,
    ) -> None:
        room, parent_transaction_id, debt_id = booked_room
        kwargs = {"room_slug": room.slug}
        if url_name.startswith("transaction:") and url_name.split(":")[1] in {"detail", "edit"}:
            kwargs["pk"] = parent_transaction_id
        if url_name == "debt:settle":
            kwargs["pk"] = debt_id
        _login(page, base_url, unrelated_user.email, DEFAULT_PASSWORD)

        response = page.goto(f"{base_url}{reverse(url_name, kwargs=kwargs)}")

        assert response is not None
        assert response.status == HTTPStatus.FORBIDDEN
        assert not Debt.objects.filter(room=room, settled=True).exists()

    def test_a_member_still_reaches_the_pages(
        self, page: Page, base_url: str, booked_room: tuple[Room, int, int], roommate: User
    ) -> None:
        room, _, _ = booked_room
        _login(page, base_url, roommate.email, DEFAULT_PASSWORD)

        response = page.goto(f"{base_url}{reverse('transaction:list', kwargs={'room_slug': room.slug})}")

        assert response is not None
        assert response.status == HTTPStatus.OK
