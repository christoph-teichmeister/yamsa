import http

import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from apps.account.tests.factories import UserFactory
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestDebtListView:
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
