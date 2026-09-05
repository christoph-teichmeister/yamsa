import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.constants import TRANSACTION_FEED_PAGE_SIZE
from apps.transaction.models import Category
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestTransactionFeedView:
    def test_transaction_feed_displays_no_matches_message(self, client, room, user, guest_user):
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
        )
        client.force_login(user)

        response = client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"q": "missing"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert 'No transactions match "missing".' in content

    def test_feed_filters_by_category(self, authenticated_client, room, user, guest_user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"description": "Weekly groceries", "category": groceries},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"description": "Train ticket", "category": transport},
        )

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"category": groceries.slug},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert "Weekly groceries" in content
        assert "Train ticket" not in content

    def test_feed_filters_by_currency(self, authenticated_client, room, user, guest_user):
        other_currency = CurrencyFactory(code="ALT")
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"description": "Preferred currency spend"},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"description": "Foreign currency spend", "currency": other_currency},
        )

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"currency": other_currency.code.lower()},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert "Foreign currency spend" in content
        assert "Preferred currency spend" not in content

    def test_feed_displays_filter_specific_empty_message(self, authenticated_client, room, user, guest_user):
        transport = Category.objects.get(slug="transport")
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user,),
            parent_transaction_kwargs={"category": transport},
        )

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"category": "groceries"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        assert "No transactions match the active filter." in response.content.decode()

    def test_feed_keeps_filters_on_the_next_batch_link(self, authenticated_client, room, user, guest_user):
        groceries = Category.objects.get(slug="groceries")
        for index in range(TRANSACTION_FEED_PAGE_SIZE):
            create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user,),
                parent_transaction_kwargs={"description": f"Groceries {index}", "category": groceries},
            )

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"category": groceries.slug},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        next_batch_trigger = soup.select_one("#transaction-batch-trigger")
        assert next_batch_trigger is not None
        assert f"category={groceries.slug}" in next_batch_trigger["hx-get"]

    def test_feed_combines_search_and_category_filter(self, authenticated_client, room, user, guest_user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")
        for description, category in (
            ("Market groceries", groceries),
            ("Market ticket", transport),
            ("Corner shop groceries", groceries),
        ):
            create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user,),
                parent_transaction_kwargs={"description": description, "category": category},
            )

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"q": "Market", "category": groceries.slug},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # Both narrowings have to apply — neither may replace the other.
        assert "Market groceries" in content
        assert "Market ticket" not in content
        assert "Corner shop groceries" not in content

    def test_feed_ignores_an_absurdly_long_filter_value(self, authenticated_client, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        response = authenticated_client.get(
            reverse("transaction:feed", kwargs={"room_slug": room.slug}),
            data={"category": "x" * 5000},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == http.HTTPStatus.OK
        # Truncated to the slug column's own limit before it can be echoed back into the UI.
        assert "x" * 200 not in response.content.decode()
