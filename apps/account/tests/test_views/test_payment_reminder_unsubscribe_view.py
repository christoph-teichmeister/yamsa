from urllib.parse import parse_qs, urlparse

from django.urls import reverse

from apps.account.utils.notification_preferences import (
    PAYMENT_REMINDER_VARIANT,
    ROOM_REMINDER_VARIANT,
    build_payment_reminder_unsubscribe_url,
)
from apps.core.tests.setup import BaseTestSetUp


class PaymentReminderUnsubscribeViewTestCase(BaseTestSetUp):
    def test_valid_token_unsubscribes_user(self):
        url = build_payment_reminder_unsubscribe_url(self.user)
        query = parse_qs(urlparse(url).query)
        token = query["token"][0]
        variant = query["variant"][0]
        self.assertEqual(variant, PAYMENT_REMINDER_VARIANT)

        response = self.client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token={token}")

        self.user.refresh_from_db()
        self.assertFalse(self.user.wants_to_receive_payment_reminders)
        self.assertContains(response, "You are no longer subscribed to payment reminder emails.")

    def test_room_variant_unsubscribes_room_reminders(self):
        url = build_payment_reminder_unsubscribe_url(self.user, variant=ROOM_REMINDER_VARIANT)
        query = parse_qs(urlparse(url).query)
        token = query["token"][0]
        variant = query["variant"][0]
        self.assertEqual(variant, ROOM_REMINDER_VARIANT)

        self.user.wants_to_receive_room_reminders = True
        self.user.save(update_fields=["wants_to_receive_room_reminders"])

        response = self.client.get(
            f"{reverse('account:payment-reminder-unsubscribe')}?token={token}&variant={ROOM_REMINDER_VARIANT}"
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.wants_to_receive_room_reminders)
        self.assertContains(response, "You are no longer receiving room reminders.")

    def test_invalid_token_shows_error_message(self):
        response = self.client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token=invalid-token")

        self.user.refresh_from_db()
        self.assertTrue(self.user.wants_to_receive_payment_reminders)
        self.assertContains(response, "expired or is invalid")
