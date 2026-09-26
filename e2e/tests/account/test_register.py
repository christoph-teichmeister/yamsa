from decimal import Decimal

import pytest
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.debt.models import Debt
from apps.room.models import UserConnectionToRoom
from e2e.pages.login_page import LoginPage
from e2e.pages.register_page import RegisterPage


@pytest.mark.e2e
class TestRegister:
    def test_a_visitor_from_a_share_link_joins_the_room_by_registering(self, shared_room, page, base_url):
        page.goto(f"{base_url}{reverse('room:share', kwargs={'share_hash': shared_room.share_hash})}")
        page.get_by_role("link", name="Create a free account").click()

        RegisterPage(page, base_url).register(name="Rita Reg", email="rita@yamsa.local", password=DEFAULT_PASSWORD)

        page.wait_for_url(lambda url: url.endswith(reverse("core:welcome")))
        rita = User.objects.get(email="rita@yamsa.local")
        assert not rita.is_guest
        assert UserConnectionToRoom.objects.filter(user=rita, room=shared_room).exists()

    def test_a_guest_keeps_their_history_when_registering_from_the_invitation(
        self, shared_room, guest_user, profile_user, page, base_url
    ):
        shared_room.users.add(guest_user)
        Debt.objects.create(
            room=shared_room,
            debitor=guest_user,
            creditor=profile_user,
            value=Decimal("9.00"),
            currency=shared_room.preferred_currency,
        )
        # The link the invitation mail carries (InvitationMailService).
        page.goto(f"{base_url}{reverse('account:register')}?with_email=gast@yamsa.local&for_guest={guest_user.id}")

        RegisterPage(page, base_url).register(name="Gabi Gast", email=None, password=DEFAULT_PASSWORD)
        page.wait_for_url(lambda url: url.endswith(reverse("core:welcome")))

        converted = User.objects.get(id=guest_user.id)
        assert (converted.email, converted.name, converted.is_guest) == ("gast@yamsa.local", "Gabi Gast", False)
        assert Debt.objects.filter(room=shared_room, debitor=converted).exists()
        assert shared_room.users.filter(id=converted.id).exists()

        # The account now signs in with the password it was given.
        page.context.clear_cookies()
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login("gast@yamsa.local", DEFAULT_PASSWORD)
