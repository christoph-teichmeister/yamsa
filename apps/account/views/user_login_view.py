from django.conf import settings
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import generic

from apps.account.forms import LoginForm


class LogInUserView(generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm

    class ExceptionMessage:
        AUTH_FAILED = "The combination of email and password does not match"

    def get_success_url(self):
        return reverse(viewname="core:welcome")

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        possible_user = authenticate(
            request=self.request, email=cleaned_data["email"], password=cleaned_data["password"]
        )

        if possible_user is not None:
            login(request=self.request, user=possible_user)
            if cleaned_data.get("remember_me"):
                self.request.session.set_expiry(settings.DJANGO_REMEMBER_ME_SESSION_AGE)
        else:
            self.extra_context = {"errors": {"auth_failed": self.ExceptionMessage.AUTH_FAILED}}
            return super().form_invalid(form)

        return super().form_valid(form)
