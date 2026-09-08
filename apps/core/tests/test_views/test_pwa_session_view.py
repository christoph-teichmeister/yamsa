import json

import pytest
from django.urls import reverse

from apps.core.pwa_constants import ANONYMOUS_SCOPE
from apps.core.services.pwa_scope_service import resolve_scope

pytestmark = pytest.mark.django_db


def test_it_hands_out_a_token_for_the_current_session(authenticated_client, user):
    """The token captured with a queued form belongs to the session that rendered it."""
    response = authenticated_client.get(reverse("core:pwa-session"))

    payload = json.loads(response.content)
    assert payload["csrf_token"]
    assert payload["scope"] == resolve_scope(user)


def test_a_signed_out_visitor_is_named_as_such(client):
    """This is what stops a queued entry being replayed under whoever signed in since."""
    payload = json.loads(client.get(reverse("core:pwa-session")).content)

    assert payload["scope"] == ANONYMOUS_SCOPE


def test_the_token_is_accepted_by_a_form_post(authenticated_client, room, user):
    """A token the views refuse would strand the queue instead of draining it."""
    from datetime import UTC, datetime

    from apps.transaction.models import Category, ParentTransaction

    token = json.loads(authenticated_client.get(reverse("core:pwa-session")).content)["csrf_token"]

    response = authenticated_client.post(
        reverse("transaction:create", kwargs={"room_slug": room.slug}),
        data={
            "csrfmiddlewaretoken": token,
            "category": Category.objects.get(slug="groceries").id,
            "description": "Replayed",
            "currency": room.preferred_currency.id,
            "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
            "paid_by": user.id,
            "room": room.id,
            "paid_for": [str(member.id) for member in room.users.all()],
            "room_slug": room.slug,
            "value": 10,
        },
    )

    assert response.status_code == 302
    assert ParentTransaction.objects.filter(description="Replayed").exists()
