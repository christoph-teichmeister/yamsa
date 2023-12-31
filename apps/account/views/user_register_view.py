from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.account.forms import RegisterForm
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.core.event_loop.runner import handle_message


class RegisterUserView(generic.CreateView):
    template_name = "account/register.html"
    form_class = RegisterForm

    @context
    @property
    def email_from_invitation_email(self):
        return self.request.GET.get("with_email")

    def get_success_url(self):
        return reverse(viewname="core-welcome")

    def get_initial(self):
        return {
            **super().get_initial(),
            "id": self.request.GET.get("for_guest"),
            "email": self.request.GET.get("with_email"),
        }

    def form_valid(self, form):
        response = super().form_valid(form)

        # Immediately log the created user in
        self.request.user = self.object
        authenticate(username=self.object.username, password=self.object.password)
        login(request=self.request, user=self.request.user)

        # Send POstRegisterEmail
        handle_message(SendPostRegisterEmail(context_data={"user": self.request.user}))

        return response
