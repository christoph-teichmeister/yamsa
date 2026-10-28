import hashlib
import logging

from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.core.utils import get_client_ip

logger = logging.getLogger(__name__)

FORGOT_PASSWORD_THROTTLE_SECONDS = 300
FORGOT_PASSWORD_IP_LIMIT = 10
FORGOT_PASSWORD_IP_WINDOW_SECONDS = 3600


class UserForgotPasswordView(generic.FormView):
    template_name = "account/forgot_password.html"
    form_class = UserForgotPasswordForm
    context_object_name = "user"

    def form_valid(self, form: UserForgotPasswordForm) -> HttpResponse:
        email = form.cleaned_data["email"].strip().lower()

        # Both limits only suppress the mail. Their counters advance whether or not the address is registered and the
        # response never changes, so neither limit tells registered and unknown addresses apart. The per-process
        # LocMemCache default counts per worker, so the real limit there is the number of workers times the value.
        ip_allowed = self._count_ip_request()
        throttle_key = "forgot-password:" + hashlib.sha256(email.encode()).hexdigest()
        email_allowed = cache.add(throttle_key, 1, FORGOT_PASSWORD_THROTTLE_SECONDS)
        if ip_allowed and email_allowed:
            for user in User.objects.filter(email__iexact=email, is_guest=False):
                handle_message(SendForgotPasswordEmail(context_data={"user": user}))

        self.request.toast_queue.info(
            _("If this address is registered, we have sent you a link to reset your password.")
        )
        return super().form_valid(form)

    def _count_ip_request(self) -> bool:
        ip = get_client_ip(self.request) or "unknown"
        key = "forgot-password-ip:" + hashlib.sha256(ip.encode()).hexdigest()
        cache.add(key, 0, FORGOT_PASSWORD_IP_WINDOW_SECONDS)
        try:
            count = cache.incr(key)
        except ValueError:  # entry expired between add and incr
            cache.set(key, 1, FORGOT_PASSWORD_IP_WINDOW_SECONDS)
            count = 1
        if count > FORGOT_PASSWORD_IP_LIMIT:
            logger.warning(
                "Forgot-password mail suppressed: IP limit of %s per window reached", FORGOT_PASSWORD_IP_LIMIT
            )
            return False
        return True

    def get_success_url(self) -> str:
        return reverse(viewname="account:login")
