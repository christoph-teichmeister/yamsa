from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse

from apps.account.utils.notification_preferences import (
    PAYMENT_REMINDER_VARIANT,
    ROOM_REMINDER_VARIANT,
    build_payment_reminder_unsubscribe_url,
)

pytestmark = pytest.mark.django_db


def test_valid_token_unsubscribes_user(client, user):
    url = build_payment_reminder_unsubscribe_url(user)
    query = parse_qs(urlparse(url).query)
    token = query["token"][0]
    variant = query["variant"][0]
    assert variant == PAYMENT_REMINDER_VARIANT

    response = client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token={token}")

    user.refresh_from_db()
    assert not user.wants_to_receive_payment_reminders
    assert "You are no longer subscribed to payment reminder emails." in response.content.decode()


def test_room_variant_unsubscribes_room_reminders(client, user):
    url = build_payment_reminder_unsubscribe_url(user, variant=ROOM_REMINDER_VARIANT)
    query = parse_qs(urlparse(url).query)
    token = query["token"][0]
    variant = query["variant"][0]
    assert variant == ROOM_REMINDER_VARIANT

    user.wants_to_receive_room_reminders = True
    user.save(update_fields=["wants_to_receive_room_reminders"])

    response = client.get(
        f"{reverse('account:payment-reminder-unsubscribe')}?token={token}&variant={ROOM_REMINDER_VARIANT}"
    )

    user.refresh_from_db()
    assert not user.wants_to_receive_room_reminders
    assert "You are no longer receiving room reminders." in response.content.decode()


def test_invalid_token_shows_error_message(client, user):
    response = client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token=invalid-token")

    user.refresh_from_db()
    assert user.wants_to_receive_payment_reminders
    assert "expired or is invalid" in response.content.decode()
