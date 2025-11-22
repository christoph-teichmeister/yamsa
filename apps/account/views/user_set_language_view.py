from django.conf import settings
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.i18n import set_language as django_set_language


@method_decorator(require_POST, name="dispatch")
class SetLanguageView(View):
    def post(self, request, *args, **kwargs):
        language = request.POST.get("language")
        response = django_set_language(request)
        if request.user.is_authenticated and language in dict(settings.LANGUAGES):
            if request.user.language != language:
                request.user.language = language
                request.user.save(update_fields=("language",))

            translation.activate(language)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

        return response
