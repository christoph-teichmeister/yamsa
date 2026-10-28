import hashlib

from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.models import User
from apps.core.event_loop.runner import handle_message

FORGOT_PASSWORD_THROTTLE_SECONDS = 300


class UserForgotPasswordView(generic.FormView):
    template_name = "account/forgot_password.html"
    form_class = UserForgotPasswordForm
    context_object_name = "user"

    def form_valid(self, form: UserForgotPasswordForm) -> HttpResponse:
        email = form.cleaned_data["email"].strip().lower()

        # One mail per address per window, so the form cannot be used to flood a mailbox. The cache entry is
        # written whether or not the address is registered, so the response never tells the two apart.
        throttle_key = "forgot-password:" + hashlib.sha256(email.encode()).hexdigest()
        if cache.add(throttle_key, 1, FORGOT_PASSWORD_THROTTLE_SECONDS):
            for user in User.objects.filter(email__iexact=email, is_guest=False):
                handle_message(SendForgotPasswordEmail(context_data={"user": user}))

        self.request.toast_queue.info(
            _("If this address is registered, we have sent you a link to reset your password.")
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(viewname="account:login")
