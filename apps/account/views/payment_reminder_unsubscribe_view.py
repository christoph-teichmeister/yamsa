from django.core.signing import BadSignature
from django.http import HttpRequest, HttpResponse
from django.views import generic

from apps.account.models import User
from apps.account.utils.notification_preferences import (
    PAYMENT_REMINDER_VARIANT,
    ROOM_REMINDER_VARIANT,
    decode_payment_reminder_unsubscribe_token,
    normalize_reminder_variant,
)

REMINDER_VARIANT_TO_FIELD = {
    PAYMENT_REMINDER_VARIANT: "wants_to_receive_payment_reminders",
    ROOM_REMINDER_VARIANT: "wants_to_receive_room_reminders",
}

REMINDER_VARIANT_SUCCESS_MESSAGE = {
    PAYMENT_REMINDER_VARIANT: "You are no longer subscribed to payment reminder emails.",
    ROOM_REMINDER_VARIANT: "You are no longer receiving room reminders.",
}


REMINDER_VARIANT_CONFIRM_MESSAGE = {
    PAYMENT_REMINDER_VARIANT: "Confirm that you no longer want to receive payment reminder emails.",
    ROOM_REMINDER_VARIANT: "Confirm that you no longer want to receive room reminders.",
}


class PaymentReminderUnsubscribeView(generic.TemplateView):
    """GET only asks for confirmation: mail scanners and link previews fetch links, and must not unsubscribe anyone."""

    template_name = "account/payment_reminder_unsubscribe.html"

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context.setdefault("success", False)
        context.setdefault("message", "Unable to process the unsubscribe request.")

        variant = normalize_reminder_variant(self.request.GET.get("variant"))
        token = self.request.GET.get("token")
        if not token:
            context["message"] = "The unsubscribe link is missing or invalid."
            return context

        try:
            user_pk = decode_payment_reminder_unsubscribe_token(token)
        except (BadSignature, ValueError):
            context["message"] = "That unsubscribe link is invalid."
            return context

        user = User.objects.filter(pk=user_pk).first()
        if not user:
            context["message"] = "We could not find a matching account."
            return context

        context["user_email"] = user.email
        if self.request.method != "POST":
            context["confirm"] = True
            context["message"] = REMINDER_VARIANT_CONFIRM_MESSAGE[variant]
            return context

        preference_field = REMINDER_VARIANT_TO_FIELD[variant]
        if getattr(user, preference_field):
            setattr(user, preference_field, False)
            user.save(update_fields=[preference_field])

        context["success"] = True
        context["message"] = REMINDER_VARIANT_SUCCESS_MESSAGE[variant]
        return context
