from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.urls import reverse
from django.utils import translation
from django.utils.translation import get_supported_language_variant
from django.views import View

from apps.account.constants import LANGUAGE_SESSION_KEY, SESSION_TTL_SESSION_KEY


class PasskeyLoginView(View):
    def post(self, request):
        user = authenticate(request=request)
        if user is None:
            return JsonResponse({"status": "ERR", "message": "Passkey nicht erkannt."}, status=401)

        login(request, user)

        language_code = user.language
        if language_code:
            try:
                supported_language = get_supported_language_variant(language_code)
            except LookupError:
                supported_language = None
            if supported_language:
                translation.activate(supported_language)
                request.session[LANGUAGE_SESSION_KEY] = supported_language

        request.session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)

        return JsonResponse({"status": "OK", "redirect": reverse("core:welcome")})
