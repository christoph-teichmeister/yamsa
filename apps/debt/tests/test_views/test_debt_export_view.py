import http

import pytest
from django.urls import reverse

from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestDebtExportView:
    def test_debt_export_returns_unsettled_debts(self, client, room, user, guest_user):
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        other_user = UserFactory()
        other_guest = GuestUserFactory()
        other_room = RoomFactory(created_by=other_user)
        other_room.users.add(other_user, other_guest)
        create_parent_transaction_with_optimisation(
            room=other_room,
            paid_by=other_user,
            paid_for_tuple=(other_guest,),
        )

        client.force_login(user)
        response = client.get(reverse("debt:export", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response["Content-Type"].startswith("text/csv")
        assert "attachment" in response["Content-Disposition"]

        lines = b"".join(response.streaming_content).decode("utf-8").splitlines()
        assert lines[0].startswith("Room Slug,")
        assert lines[1].startswith("Room Name,")
        assert lines[2].startswith("Export Timestamp,")
        assert lines[3] == ""
        assert lines[4] == "debitor,creditor,amount,currency,settled,settled_at"

        data_rows = [line for line in lines[5:] if line]
        assert data_rows
        assert user.name in data_rows[0] or guest_user.name in data_rows[0]

    def test_debt_export_requires_membership(self, client, room):
        outsider = UserFactory()
        client.force_login(outsider)
        response = client.get(reverse("debt:export", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
