import http

import pytest
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestDebtListView:
    def test_debt_row_shows_both_sides_of_the_debt(self, client, room, user, guest_user, attach_profile_picture):
        attach_profile_picture(user)
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        client.force_login(user)

        response = client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        pair = BeautifulSoup(response.content.decode(), "html.parser").select_one(".avatar-pair")
        assert pair is not None

        debitor_avatar, creditor_avatar = pair.select(".avatar")
        # The guest has no picture, the creditor does - the row shows an initial next to a photo.
        assert debitor_avatar.find("img") is None
        assert debitor_avatar.get_text(strip=True) == guest_user.name[:1].upper()
        assert creditor_avatar.find("img")["src"] == user.avatar_url

    def test_debt_list_renders_outstanding_debt_and_counts(self, client, room, user, guest_user):
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        response = client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data
        assert context["has_transactions"] is True
        assert context["active_debt_count"] == room.debts.filter(settled=False).count()
        assert context["active_debt_count"] == 1

        debts = list(context["debts"])
        assert debts
        assert any(not debt.settled for debt in debts)
        outstanding_debt = next(debt for debt in debts if not debt.settled)
        assert outstanding_debt.debitor_id == guest_user.id
        assert outstanding_debt.creditor_id == user.id

    def test_debt_list_updates_when_settlement_creates_new_debt(self, client, room, user, guest_user):
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )

        debt_to_settle = room.debts.filter(settled=False).first()
        debt_to_settle.settled = True
        debt_to_settle.settled_at = timezone.now().date()
        debt_to_settle.save()

        new_user = UserFactory()
        room.users.add(new_user)

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(new_user,),
        )

        response = client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data
        assert context["has_transactions"] is True
        assert context["active_debt_count"] == room.debts.filter(settled=False).count()
        assert context["active_debt_count"] == 1

        debts = list(context["debts"])
        assert debts
        assert any(debt.settled for debt in debts)
        unsettled_debts = [debt for debt in debts if not debt.settled]
        assert unsettled_debts
        assert any(debt.debitor_id == new_user.id for debt in unsettled_debts)
        assert any(debt.creditor_id == guest_user.id for debt in unsettled_debts)

    def test_debt_list_shows_empty_state_without_transactions(self, authenticated_client, room):
        response = authenticated_client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data
        assert list(context["debts"]) == []
        assert context["active_debt_count"] == 0
        assert context["has_transactions"] is False
        context_dict = context.flatten() if hasattr(context, "flatten") else dict(context)
        rendered_html = render_to_string("debt/list.html", context_dict, request=response.wsgi_request)
        assert gettext("No debts yet") in rendered_html

    def test_debt_list_defaults_to_the_optimised_mode(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["debt_mode"] == "optimised"
        assert response.context_data["showing_optimised_debts"] is True

    def test_unknown_mode_falls_back_to_the_optimised_mode(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(
            reverse("debt:list", kwargs={"room_slug": room.slug}), data={"mode": "nonsense"}
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["showing_optimised_debts"] is True

    def test_simple_mode_lists_the_unnetted_debts(self, authenticated_client, room, user, guest_user):
        """Two expenses that cancel each other out leave no optimised debt, but two simple rows."""
        currency = CurrencyFactory()
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"currency": currency},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(user,),
            parent_transaction_kwargs={"currency": currency},
        )
        assert room.debts.count() == 0

        response = authenticated_client.get(
            reverse("debt:list", kwargs={"room_slug": room.slug}), data={"mode": "simple"}
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.context_data["showing_optimised_debts"] is False
        rows = list(response.context_data["debts"])
        assert {(row.debitor.id, row.creditor.id) for row in rows} == {
            (guest_user.id, user.id),
            (user.id, guest_user.id),
        }

    def test_simple_mode_offers_no_settle_action(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=guest_user, paid_for_tuple=(user,))
        list_url = reverse("debt:list", kwargs={"room_slug": room.slug})

        optimised_html = authenticated_client.get(list_url).content.decode()
        simple_html = authenticated_client.get(list_url, data={"mode": "simple"}).content.decode()

        # The viewer owes money in both readings, so the settle button is missing because of the
        # mode - not because there is nothing of theirs to settle.
        assert gettext("Mark as paid") in optimised_html
        assert gettext("Mark as paid") not in simple_html

    def test_payment_count_comparison_counts_both_readings(self, authenticated_client, room, user, guest_user):
        third_user = UserFactory()
        room.users.add(third_user)
        currency = CurrencyFactory()
        # user fronts both shares, then guest_user covers third_user - which nets guest_user out
        # entirely and turns the three direct repayments into a single one.
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, third_user),
            parent_transaction_kwargs={"currency": currency},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(third_user,),
            parent_transaction_kwargs={"currency": currency},
        )

        response = authenticated_client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        comparison = response.context_data["payment_count_comparison"]
        assert comparison == {"optimised": 1, "simple": 3}

    def test_payment_count_comparison_is_dropped_once_a_debt_is_settled(
        self, authenticated_client, room, user, guest_user
    ):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        debt = room.debts.get()
        debt.settled = True
        debt.settled_at = timezone.now().date()
        debt.save()

        response = authenticated_client.get(reverse("debt:list", kwargs={"room_slug": room.slug}))

        assert response.context_data["payment_count_comparison"] is None
