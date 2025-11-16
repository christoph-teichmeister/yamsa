from django.core.signing import BadSignature
from django.views import generic

from apps.account.models import User
from apps.account.utils.notification_preferences import decode_payment_reminder_unsubscribe_token


class PaymentReminderUnsubscribeView(generic.TemplateView):
    template_name = "account/payment_reminder_unsubscribe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("success", False)
        context.setdefault("message", "Unable to process the unsubscribe request.")

        token = self.request.GET.get("token")
        if not token:
            context["message"] = "The unsubscribe link is missing or invalid."
            return context

        try:
            user_pk = decode_payment_reminder_unsubscribe_token(token)
        except (BadSignature, ValueError):
            context["message"] = "That unsubscribe link has expired or is invalid."
            return context

        user = User.objects.filter(pk=user_pk).first()
        if not user:
            context["message"] = "We could not find a matching account."
            return context

        if user.wants_to_receive_payment_reminders:
            user.wants_to_receive_payment_reminders = False
            user.save(update_fields=["wants_to_receive_payment_reminders"])

        context["success"] = True
        context["message"] = "You are no longer subscribed to payment reminder emails."
        context["user_email"] = user.email
        return context
