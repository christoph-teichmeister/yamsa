from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import get_supported_language_variant
from django.utils.translation import gettext_lazy as _
from django.views import generic

from apps.account.constants import LANGUAGE_SESSION_KEY, SESSION_TTL_SESSION_KEY
from apps.account.forms import LoginForm


class LogInUserView(generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm

    class ExceptionMessage:
        AUTH_FAILED = _("The combination of email and password does not match")

    def get_success_url(self) -> str:
        return self.next_url or reverse(viewname="core:welcome")

    @property
    def next_url(self) -> str:
        """The page that sent the visitor to the login, or "" unless it stays on this host."""
        candidate = self.request.POST.get("next") or self.request.GET.get("next") or ""
        is_safe = url_has_allowed_host_and_scheme(
            candidate, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
        )
        return candidate if is_safe else ""

    def get_context_data(self, **kwargs: object) -> dict:
        return {**super().get_context_data(**kwargs), "next_url": self.next_url}

    def form_valid(self, form: LoginForm) -> HttpResponse:
        cleaned_data = form.cleaned_data
        possible_user = authenticate(
            request=self.request, email=cleaned_data["email"], password=cleaned_data["password"]
        )

        if possible_user is not None:
            login(request=self.request, user=possible_user)
            language_code = possible_user.language
            if language_code:
                try:
                    supported_language = get_supported_language_variant(language_code)
                except LookupError:
                    supported_language = None
                if supported_language:
                    translation.activate(supported_language)
                    self.request.session[LANGUAGE_SESSION_KEY] = supported_language
            target_ttl = settings.SESSION_COOKIE_AGE
            if cleaned_data.get("remember_me"):
                target_ttl = settings.DJANGO_REMEMBER_ME_SESSION_AGE
            self._apply_session_ttl(ttl=target_ttl)
        else:
            self.extra_context = {"errors": {"auth_failed": self.ExceptionMessage.AUTH_FAILED}}
            return super().form_invalid(form)

        return super().form_valid(form)

    def _apply_session_ttl(self, *, ttl: int) -> None:
        session = self.request.session
        session[SESSION_TTL_SESSION_KEY] = ttl
        session.set_expiry(ttl)
