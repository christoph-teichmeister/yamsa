from django.contrib.auth import authenticate, login, hashers
from django.urls import reverse
from django.views import generic

from apps.account.forms import RegisterForm
from apps.account.models import User


class RegisterUserView(generic.FormView):
    template_name = "account/register.html"
    form_class = RegisterForm

    def get_success_url(self):
        return reverse(viewname="core-welcome")

    def form_valid(self, form):
        if self.request.user.is_anonymous:
            user = User.objects.create_user(
                username=form.data["username"],
                password=form.data["password"],
                name=form.data["username"],
                email=form.data["email"],
                is_guest=False,
            )
        else:
            user = self.request.user
            user.username = form.data["username"]
            user.name = form.data["username"]
            user.email = form.data["email"]
            user.password = hashers.make_password(form.data["password"])
            user.is_guest = False

            user.save()

        user = authenticate(username=user.username, password=user.password)

        login(request=self.request, user=user)

        return super().form_valid(form)
