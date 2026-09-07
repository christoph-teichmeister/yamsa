import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestDebtSettleView:
    def test_post_closed_room_is_rejected(self, authenticated_client, closed_room, user, guest_user):
        create_parent_transaction_with_optimisation(
            room=closed_room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )
        debt = closed_room.debts.filter(settled=False).first()

        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": closed_room.slug, "pk": debt.pk}),
            data={"id": debt.pk, "settled": "on"},
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        debt.refresh_from_db()
        assert debt.settled is False

    def test_settle_page_shows_the_creditor(self, client, room, user, guest_user, attach_profile_picture):
        attach_profile_picture(user)
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        debt = room.debts.filter(settled=False).first()
        client.force_login(guest_user)

        response = client.get(reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.pk}))

        assert response.status_code == http.HTTPStatus.OK
        avatar = BeautifulSoup(response.content.decode(), "html.parser").select_one(".avatar")
        assert avatar.find("img")["src"] == debt.creditor.avatar_url
