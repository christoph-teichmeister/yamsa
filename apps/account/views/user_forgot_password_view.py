from django.urls import reverse
from django.views import generic

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.models import User
from apps.core.event_loop.runner import handle_message


class UserForgotPasswordView(generic.FormView):
    template_name = "account/forgot_password.html"
    form_class = UserForgotPasswordForm
    context_object_name = "user"

    def form_valid(self, form):
        form_valid = super().form_valid(form)

        user = User.objects.get(email=form.cleaned_data["email"])

        handle_message(SendForgotPasswordEmail(context_data={"user": user}))

        return form_valid

    def get_success_url(self):
        return reverse(viewname="account:login")
