from urllib.parse import parse_qs, urlparse

from django.urls import reverse

from apps.account.utils.notification_preferences import build_payment_reminder_unsubscribe_url
from apps.core.tests.setup import BaseTestSetUp


class PaymentReminderUnsubscribeViewTestCase(BaseTestSetUp):
    def test_valid_token_unsubscribes_user(self):
        url = build_payment_reminder_unsubscribe_url(self.user)
        token = parse_qs(urlparse(url).query)["token"][0]
        response = self.client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token={token}")

        self.user.refresh_from_db()
        self.assertFalse(self.user.wants_to_receive_payment_reminders)
        self.assertContains(response, "You are no longer subscribed to payment reminder emails.")

    def test_invalid_token_shows_error_message(self):
        response = self.client.get(f"{reverse('account:payment-reminder-unsubscribe')}?token=invalid-token")

        self.user.refresh_from_db()
        self.assertTrue(self.user.wants_to_receive_payment_reminders)
        self.assertContains(response, "expired or is invalid")
