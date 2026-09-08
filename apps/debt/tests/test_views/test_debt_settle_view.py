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

    def test_paypal_link_carries_the_amount_and_currency(self, client, room, user, guest_user):
        """Regression: the paypal.me short link drops the amount segment on redirect."""
        user.paypal_me_username = "creditorname"
        user.save()
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        debt = room.debts.filter(settled=False).first()
        client.force_login(guest_user)

        response = client.get(reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.pk}))

        assert response.status_code == http.HTTPStatus.OK
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        paypal_link = soup.select_one('a[href*="paypal"]')
        assert paypal_link is not None
        assert paypal_link["href"] == (f"https://www.paypal.com/paypalme/creditorname/{debt.value}{debt.currency.code}")
