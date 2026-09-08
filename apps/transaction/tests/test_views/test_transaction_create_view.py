import http
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from freezegun import freeze_time

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.views import TransactionListView

pytestmark = pytest.mark.django_db


class TestTransactionCreateView:
    @freeze_time("2020-04-04 4:20:00")
    def test_post_regular(self, authenticated_client, room, user):
        assert room.users.count() > 1, "This test requires more than one participant in the room"

        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "category": Category.objects.get(slug="groceries").id,
                "description": "My description",
                "currency": room.preferred_currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": user.id,
                "room": room.id,
                "paid_for": [str(member.id) for member in room.users.all()],
                "room_slug": room.slug,
                "value": 10,
            },
            follow=True,
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == TransactionListView.template_name
        assert "Room transactions" in response.content.decode()
        assert response.context_data["active_tab"] == "transaction"

        assert ParentTransaction.objects.filter(description="My description", room=room, paid_by=user).exists()
        parent_transaction = ParentTransaction.objects.get(description="My description", room=room, paid_by=user)
        assert parent_transaction.value == Decimal("10")

        child_transaction_value = Decimal("10") / room.users.count()
        for member in room.users.all():
            qs = ChildTransaction.objects.filter(paid_for=member, value=child_transaction_value)
            assert qs.exists()

    def test_get_renders_a_chip_per_category_without_preselecting_one(self, authenticated_client, room):
        response = authenticated_client.get(reverse("transaction:create", kwargs={"room_slug": room.slug}))
        category_field = self._category_field(response)

        categories = list(RoomCategoryService(room=room).get_category_queryset())
        assert categories
        for category in categories:
            assert category.name in category_field.get_text()
            assert category.emoji in category_field.get_text()

        assert len(category_field.select("input[type='radio'][data-category-slug]")) == len(categories)
        # Nothing is preselected: the user has to pick a category deliberately.
        assert category_field.select("input[type='radio'][checked]") == []

    @staticmethod
    def _category_field(response):
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        return soup.select_one("[data-category-field]")

    def test_get_offers_a_way_into_the_category_manager(self, authenticated_client, room):
        response = authenticated_client.get(reverse("transaction:create", kwargs={"room_slug": room.slug}))

        manager_url = reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        assert manager_url in response.content.decode()

    def test_get_exposes_the_category_suggestion_index(self, authenticated_client, room):
        response = authenticated_client.get(reverse("transaction:create", kwargs={"room_slug": room.slug}))

        index = json.loads(response.context_data["category_suggestion_index"])
        assert index["rewe"] == Category.objects.get(slug="groceries").id
        assert "data-category-suggestion-index" in response.content.decode()

    def test_post_without_a_category_is_rejected(self, authenticated_client, room, user):
        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data={
                "description": "Uncategorised",
                "currency": room.preferred_currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": user.id,
                "room": room.id,
                "paid_for": [str(member.id) for member in room.users.all()],
                "room_slug": room.slug,
                "value": 10,
            },
        )

        assert response.status_code == http.HTTPStatus.OK
        assert not ParentTransaction.objects.filter(description="Uncategorised").exists()

    def test_post_closed_room_is_rejected(self, authenticated_client, closed_room, user):
        response = authenticated_client.post(
            reverse("transaction:create", kwargs={"room_slug": closed_room.slug}),
            data={
                "description": "My description",
                "currency": closed_room.preferred_currency.id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": user.id,
                "room": closed_room.id,
                "paid_for": [str(member.id) for member in closed_room.users.all()],
                "room_slug": closed_room.slug,
                "value": 10,
            },
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert not ParentTransaction.objects.filter(description="My description", room=closed_room).exists()

    @staticmethod
    def _valid_payload(room, user, **overrides):
        payload = {
            "category": Category.objects.get(slug="groceries").id,
            "description": "My description",
            "currency": room.preferred_currency.id,
            "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
            "paid_by": user.id,
            "room": room.id,
            "paid_for": [str(member.id) for member in room.users.all()],
            "room_slug": room.slug,
            "value": 10,
        }
        payload.update(overrides)
        return payload

    def test_the_form_carries_a_name_for_the_submission(self, authenticated_client, room):
        """Minted server-side, so a submission that never reaches JavaScript carries one too."""
        response = authenticated_client.get(reverse("transaction:create", kwargs={"room_slug": room.slug}))

        field = BeautifulSoup(response.content, "html.parser").select_one('input[name="client_request_id"]')
        assert field is not None
        assert uuid.UUID(field["value"])

    def test_replaying_a_submission_books_the_expense_once(self, authenticated_client, room, user):
        """What an offline queue does when the first attempt reached the server after all."""
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})
        client_request_id = str(uuid.uuid4())
        payload = self._valid_payload(room, user, client_request_id=client_request_id)

        first = authenticated_client.post(url, data=payload)
        with patch("apps.transaction.views.transaction_create_view.handle_message") as replayed_message:
            second = authenticated_client.post(url, data=payload)

        assert first.status_code == http.HTTPStatus.FOUND
        assert second.status_code == http.HTTPStatus.FOUND
        assert second["Location"] == first["Location"]
        assert ParentTransaction.objects.filter(client_request_id=client_request_id).count() == 1
        # Debts were recalculated and everyone was notified when it was created.
        replayed_message.assert_not_called()

    def test_a_replay_adds_no_second_split(self, authenticated_client, room, user):
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})
        payload = self._valid_payload(room, user, client_request_id=str(uuid.uuid4()))

        authenticated_client.post(url, data=payload)
        authenticated_client.post(url, data=payload)

        assert ChildTransaction.objects.count() == room.users.count()

    def test_two_submissions_of_the_same_expense_are_both_booked(self, authenticated_client, room, user):
        """Only a replay of one submission is folded away, not a visitor entering it twice."""
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})

        authenticated_client.post(url, data=self._valid_payload(room, user, client_request_id=str(uuid.uuid4())))
        authenticated_client.post(url, data=self._valid_payload(room, user, client_request_id=str(uuid.uuid4())))

        assert ParentTransaction.objects.filter(description="My description").count() == 2

    def test_a_replay_that_slips_past_the_check_is_still_booked_once(self, authenticated_client, room, user):
        """The unique index is the guarantee, not the lookup - two replays can race each other.

        Blinding the lookup is how the test reaches the path that a real race takes, where the
        first submission lands between the check and the save.
        """
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})
        payload = self._valid_payload(room, user, client_request_id=str(uuid.uuid4()))
        authenticated_client.post(url, data=payload)

        with patch("apps.transaction.views.transaction_create_view.ParentTransaction") as blinded:
            blinded.objects.filter.return_value.exists.return_value = False
            response = authenticated_client.post(url, data=payload)

        assert response.status_code == http.HTTPStatus.FOUND
        assert ParentTransaction.objects.filter(description="My description").count() == 1

    def test_a_submission_without_a_name_is_still_booked(self, authenticated_client, room, user):
        """The field is the client's to send; a form posted without it may not be refused."""
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})

        response = authenticated_client.post(url, data=self._valid_payload(room, user))

        assert response.status_code == http.HTTPStatus.FOUND
        assert ParentTransaction.objects.filter(description="My description").count() == 1

    def test_an_unusable_name_does_not_cost_the_expense(self, authenticated_client, room, user):
        url = reverse("transaction:create", kwargs={"room_slug": room.slug})

        response = authenticated_client.post(url, data=self._valid_payload(room, user, client_request_id="nonsense"))

        assert response.status_code == http.HTTPStatus.FOUND
        assert ParentTransaction.objects.filter(description="My description").count() == 1

    def test_form_valid_fires_handle_message_outside_atomic(self):
        """
        Regression test for #333: handle_message must be called from form_valid,
        not from inside form.save() (which runs inside transaction.atomic).
        Calling it from within the atomic block held the DB connection open
        during webpush HTTP requests, blocking consecutive saves.
        """
        from unittest.mock import MagicMock

        from django.utils import timezone

        from apps.transaction.views.transaction_create_view import TransactionCreateView

        user = UserFactory()
        other_user = UserFactory()
        room = RoomFactory(created_by=user)
        room.users.add(user, other_user)
        currency = CurrencyFactory()

        view = TransactionCreateView()
        view.request = MagicMock(user=user, room=room, method="POST")
        view.kwargs = {"room_slug": room.slug}
        view.object = None

        form = TransactionCreateForm(
            data={
                "category": Category.objects.get(slug="groceries").id,
                "description": "Test",
                "currency": currency.id,
                "paid_at": timezone.now(),
                "paid_by": user.id,
                "room": room.id,
                "paid_for": [user.id, other_user.id],
                "room_slug": room.slug,
                "value": "10.00",
            },
            request=MagicMock(user=user),
            room=room,
        )
        assert form.is_valid(), form.errors

        with patch("apps.transaction.views.transaction_create_view.handle_message") as mock_handle:
            view.form_valid(form)

        mock_handle.assert_called_once()
