from django.contrib.auth import authenticate, login, logout, hashers
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.account.forms import LoginForm, RegisterForm
from apps.account.models import User
from apps.config import settings


class UserProfileView(generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User

    def get_context_data(self, **kwargs):
        return (
            super()
            .get_context_data(**kwargs)
            .update({"PROJECT_BASE_URL": settings.PROJECT_BASE_URL})
        )


class AuthenticateGuestUserView(generic.View):
    http_method_names = [
        "post",
        "options",
    ]

    def post(self, request, *args, **kwargs):
        room_slug = self.request.POST.get("room_slug")

        redirect_response = HttpResponseRedirect(
            redirect_to=reverse(viewname="room-detail", kwargs={"slug": room_slug})
        )

        if request.user.is_authenticated:
            return redirect_response

        user_id = self.request.POST.get("user_id")
        guest_user = User.objects.get(id=user_id)
        login(request=request, user=guest_user)

        return redirect_response


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

        user = authenticate(
            username=user.username, password=user.password
        )

        login(request=self.request, user=user)

        return super().form_valid(form)


class LogInUserView(generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm

    def get_success_url(self):
        return reverse(viewname="core-welcome")

    def form_valid(self, form):
        possible_user = authenticate(
            username=form.data["username"], password=form.data["password"]
        )

        if possible_user is not None:
            login(request=self.request, user=possible_user)
        else:
            self.extra_context = {
                "errors": {
                    "auth_failed": "The combination of username and password does not match"
                }
            }
            return super().form_invalid(form)

        return super().form_valid(form)


class LogOutUserView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        logout(request=request)
        return HttpResponseRedirect(redirect_to=reverse(viewname="core-welcome"))
