from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import generic

from apps.account.forms import LoginForm


class LogInUserView(generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm

    def get_success_url(self):
        return reverse(viewname="core:welcome")

    def form_valid(self, form):
        possible_user = authenticate(username=form.data["username"], password=form.data["password"])

        if possible_user is not None:
            login(request=self.request, user=possible_user)
        else:
            self.extra_context = {"errors": {"auth_failed": "The combination of username and password does not match"}}
            return super().form_invalid(form)

        return super().form_valid(form)
