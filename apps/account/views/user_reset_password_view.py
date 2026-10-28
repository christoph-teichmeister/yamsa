from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views import generic

from apps.account.models import User


class UserResetPasswordView(generic.FormView):
    """Set a new password through the signed link from the forgot-password email."""

    template_name = "account/reset_password.html"
    form_class = SetPasswordForm

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        self.user = self._user_from_link(kwargs["uidb64"], kwargs["token"])
        if self.user is None:
            request.toast_queue.error(_("This password reset link is invalid or has expired."))
            return HttpResponseRedirect(reverse(viewname="account:forgot-password"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict:
        return {**super().get_form_kwargs(), "user": self.user}

    def form_valid(self, form: SetPasswordForm) -> HttpResponse:
        form.save()
        self.request.toast_queue.success(_("Your password has been changed. You can log in now."))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(viewname="account:login")

    @staticmethod
    def _user_from_link(uidb64: str, token: str) -> User | None:
        try:
            user = User.objects.get(pk=urlsafe_base64_decode(uidb64).decode(), is_guest=False)
        except (User.DoesNotExist, ValueError, OverflowError, UnicodeDecodeError):
            return None
        return user if default_token_generator.check_token(user, token) else None
