import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


@pytest.fixture
def foreign_room(room: Room, user: User) -> Room:
    """A second room the same user belongs to: only the slug in the URL tells the two apart."""
    foreign = RoomFactory(created_by=user)
    foreign.users.add(user)
    return foreign


class TestObjectsOfAnotherRoomAreNotReachable:
    """The URL's room slug and the object's own room must agree."""

    def test_edit_page_of_a_foreign_transaction_is_not_found(
        self, authenticated_client: Client, room: Room, foreign_room: Room, user: User, guest_user: User
    ) -> None:
        foreign_transaction, _ = create_parent_transaction_with_optimisation(
            room=foreign_room, paid_by=user, paid_for_tuple=(user,)
        )

        response = authenticated_client.get(
            reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": foreign_transaction.pk})
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND

    def test_edit_post_cannot_change_a_foreign_transaction(
        self, authenticated_client: Client, room: Room, foreign_room: Room, user: User
    ) -> None:
        foreign_transaction, _ = create_parent_transaction_with_optimisation(
            room=foreign_room, paid_by=user, paid_for_tuple=(user,)
        )

        response = authenticated_client.post(
            reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": foreign_transaction.pk}),
            data={"description": "hijacked"},
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        foreign_transaction.refresh_from_db()
        assert foreign_transaction.description != "hijacked"

    def test_detail_page_of_a_foreign_transaction_is_not_found(
        self, authenticated_client: Client, room: Room, foreign_room: Room, user: User
    ) -> None:
        foreign_transaction, _ = create_parent_transaction_with_optimisation(
            room=foreign_room, paid_by=user, paid_for_tuple=(user,)
        )

        response = authenticated_client.get(
            reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": foreign_transaction.pk})
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND

    def test_a_foreign_closed_rooms_share_cannot_be_deleted_through_an_open_room(
        self, authenticated_client: Client, room: Room, closed_room: Room, user: User, guest_user: User
    ) -> None:
        _, (_, guest_share) = create_parent_transaction_with_optimisation(
            room=closed_room, paid_by=user, paid_for_tuple=(user, guest_user)
        )

        response = authenticated_client.post(
            reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": guest_share.pk})
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        assert ChildTransaction.objects.filter(pk=guest_share.pk).exists()

    def test_a_foreign_closed_rooms_transaction_cannot_be_deleted_through_an_open_room(
        self, authenticated_client: Client, room: Room, closed_room: Room, user: User, guest_user: User
    ) -> None:
        foreign_transaction, _ = create_parent_transaction_with_optimisation(
            room=closed_room, paid_by=user, paid_for_tuple=(guest_user,)
        )

        response = authenticated_client.post(
            reverse(
                "transaction:parent-transaction-delete",
                kwargs={"room_slug": room.slug, "pk": foreign_transaction.pk},
            )
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        assert ParentTransaction.objects.filter(pk=foreign_transaction.pk).exists()

    def test_a_foreign_closed_rooms_debt_cannot_be_settled_through_an_open_room(
        self, authenticated_client: Client, room: Room, closed_room: Room, user: User, guest_user: User
    ) -> None:
        create_parent_transaction_with_optimisation(room=closed_room, paid_by=user, paid_for_tuple=(guest_user,))
        foreign_debt = Debt.objects.get(room=closed_room, settled=False)

        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": foreign_debt.pk}),
            data={"settled": "on"},
        )

        assert response.status_code == http.HTTPStatus.NOT_FOUND
        foreign_debt.refresh_from_db()
        assert foreign_debt.settled is False

    def test_a_child_transaction_cannot_be_added_to_a_foreign_transaction(
        self, authenticated_client: Client, room: Room, foreign_room: Room, user: User
    ) -> None:
        foreign_transaction, _ = create_parent_transaction_with_optimisation(
            room=foreign_room, paid_by=user, paid_for_tuple=(user,)
        )

        response = authenticated_client.post(
            reverse("transaction:child-transaction-create", kwargs={"room_slug": room.slug}),
            data={"parent_transaction": foreign_transaction.pk, "paid_for": user.pk, "value": "5.00"},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert ChildTransaction.objects.filter(parent_transaction=foreign_transaction).count() == 1
