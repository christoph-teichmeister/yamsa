from django.contrib.auth import authenticate, login, hashers
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.account.forms import RegisterForm
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.models import User
from apps.core.event_loop.runner import handle_message


class RegisterUserView(generic.FormView):
    template_name = "account/register.html"
    form_class = RegisterForm

    @context
    @property
    def email_from_invitation_email(self):
        return self.request.GET.get("with_email")

    def get_success_url(self):
        return reverse(viewname="core-welcome")

    def form_valid(self, form):
        # TODO CT: Move this to form

        referer_header = self.request.headers.get("REFERER")
        if "for_guest" in referer_header:
            # for_guest_str may look something like: "for_guest=5"
            for_guest_str = referer_header.split("&")[-1]
            guest_id = for_guest_str.split("=")[-1]

            user = User.objects.get(id=guest_id)

            user.username = form.cleaned_data["username"]
            user.name = form.cleaned_data["username"]
            user.password = hashers.make_password(form.cleaned_data["password"])
            user.email = form.cleaned_data["email"]
            user.is_guest = False

            user.save()

            self.request.user = user

        # If a guest, who is not logged in is registering...
        elif self.request.user.is_anonymous:
            # ...create a new user
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                name=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                is_guest=False,
            )
            self.request.user = user

        # Else, if a guest who is logged in as guest is registering...
        else:
            # ...update the existing guest-user
            user = self.request.user
            user.username = form.cleaned_data["username"]
            user.name = form.cleaned_data["username"]
            user.email = form.cleaned_data["email"]
            user.password = hashers.make_password(form.cleaned_data["password"])
            user.is_guest = False

            user.save()

        user = authenticate(username=user.username, password=user.password)

        login(request=self.request, user=user)

        handle_message(SendPostRegisterEmail(context_data={"user": self.request.user}))

        return super().form_valid(form)
