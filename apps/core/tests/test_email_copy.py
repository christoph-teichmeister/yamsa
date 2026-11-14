import pytest
from django.test import Client

from apps.account.models import User
from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.mail.services.payment_reminder_mail_service import PaymentReminderEmailService
from apps.mail.services.room_closure_reminder_mail_service import RoomClosureReminderEmailService

pytestmark = pytest.mark.django_db


def carried_toast_messages(client: Client) -> list[str]:
    return [toast["message"] for toast in client.session.get(ToastMiddleware.CARRIED_TOASTS_SESSION_KEY, [])]


class TestEmailCopy:
    def test_the_payment_reminder_names_the_creditor_and_stays_calm(self, user: User, guest_user: User) -> None:
        service = PaymentReminderEmailService(
            recipient=user,
            room_name="Trip",
            amount_summary="€12.00",
            creditor_names=("Alex",),
            inactivity_days=30,
            payment_link="https://example.com",
        )

        context = service.get_context_data()["context"]
        text = " ".join(str(line) for line in context["text_list"]) + context["sub_footer"]

        assert "You still owe €12.00 to Alex." in text
        assert "room admin" not in text.lower()

    def test_the_closure_reminder_does_not_ask_to_close_the_room(self, user: User) -> None:
        service = RoomClosureReminderEmailService(
            recipient=user, room_name="Trip", inactivity_days=30, room_link="https://example.com"
        )

        text = " ".join(str(line) for line in service.get_context_data()["context"]["text_list"])

        assert "stops lingering" not in text
        assert "no need to close the room" in text

    def test_the_email_speaks_the_recipients_language(self, user: User) -> None:
        user.language = "de"
        user.save()
        service = RoomClosureReminderEmailService(
            recipient=user, room_name="Trip", inactivity_days=30, room_link="https://example.com"
        )

        context = service.get_context_data()

        assert context["language_code"] == "de"
        assert context["context"]["unsubscribe_label"] == "Abbestellen"
