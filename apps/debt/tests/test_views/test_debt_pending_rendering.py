import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room

pytestmark = pytest.mark.django_db

SETTLE_MESSAGES = "apps.debt.views.debt_settle_view.handle_message"
REOPEN_MESSAGES = "apps.debt.views.debt_reopen_view.handle_message"


def settle_url(debt: Debt) -> str:
    return reverse("debt:settle", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def reopen_url(debt: Debt) -> str:
    return reverse("debt:reopen", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def login(client: Client, who: User) -> Client:
    client.force_login(who)
    return client


class TestRendering:
    def labels(self, client: Client, room: Room, who: User) -> str:
        response = login(client, who).get(reverse("debt:list", kwargs={"room_slug": room.slug}))
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        return " ".join(soup.select_one("[data-debt-row]").get_text(" ", strip=True).split())

    def test_the_debtor_sees_waiting_and_a_withdraw_button(
        self, client: Client, room: Room, pending_debt: Debt, guest_user: User
    ) -> None:
        text = self.labels(client, room, guest_user)

        assert "Paid, waiting for confirmation" in text
        assert "Withdraw" in text
        assert "Mark as paid" not in text
        assert "Confirm payment" not in text

    def test_the_creditor_sees_confirm_and_not_received(
        self, client: Client, room: Room, pending_debt: Debt, user: User
    ) -> None:
        text = self.labels(client, room, user)

        assert "Paid, waiting for confirmation" in text
        assert "Confirm payment" in text
        assert "Not received" in text

    def test_the_creditor_of_an_open_debt_can_mark_it_as_received(
        self, client: Client, room: Room, debt: Debt, user: User
    ) -> None:
        text = self.labels(client, room, user)

        assert "Mark as received" in text
        assert "waiting for confirmation" not in text

    def test_the_settle_page_speaks_to_the_creditor_about_receiving(
        self, client: Client, debt: Debt, user: User
    ) -> None:
        response = login(client, user).get(settle_url(debt))

        content = response.content.decode()
        assert "Yes, I received it" in content
        assert "Pay with PayPal" not in content
        assert "via PayPal" not in content

    def test_the_settle_page_tells_the_debtor_the_creditor_must_confirm(
        self, client: Client, debt: Debt, guest_user: User
    ) -> None:
        response = login(client, guest_user).get(settle_url(debt))

        content = response.content.decode()
        assert "has to confirm the payment" in content
        assert "Yes, I paid this" in content

    def test_the_paypal_flow_still_ends_in_the_pending_state(
        self, client: Client, debt: Debt, user: User, guest_user: User
    ) -> None:
        User.objects.filter(pk=user.pk).update(paypal_me_username="creditorname")
        login(client, guest_user)

        page = client.get(settle_url(debt)).content.decode()
        assert "https://www.paypal.com/paypalme/creditorname/" in page

        client.post(settle_url(debt), data={"settled": "true"})
        debt.refresh_from_db()
        assert (debt.settled, debt.awaiting_confirmation) == (False, True)
