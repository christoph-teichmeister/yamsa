from django.conf import settings

from apps.account.models import User


def get_language_code_for_user(user: User | None) -> str:
    language_value = user.language if user is not None else None
    valid_languages = dict(settings.LANGUAGES)
    if language_value in valid_languages:
        return language_value
    return settings.LANGUAGE_CODE
