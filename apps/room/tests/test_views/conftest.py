from collections.abc import Callable
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

STATUS_VIEW = "apps.room.views.room_status_update_view"


@pytest.fixture
def room_with_settled_and_open_debt(room: Room, user: User, guest_user: User) -> Room:
    """One honestly settled debt of 13 plus one open debt of 13 from a second expense."""
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
    Debt.objects.filter(room=room).update(settled=True)
    create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
    return room


@pytest.fixture
def post_status(authenticated_client: Client) -> Callable:
    """Post to the status endpoint with the event runner mocked; returns (response, handle_message mock)."""

    def post(room: Room, **data: str) -> tuple:
        with mock.patch(f"{STATUS_VIEW}.handle_message") as handle_message:
            response = authenticated_client.post(reverse("room:status", kwargs={"room_slug": room.slug}), data=data)
        return response, handle_message

    return post
