import pytest
from django.test import Client
from django.utils import translation

from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.room.templatetags.room_tags import money

pytestmark = pytest.mark.django_db


def carried_toast_messages(client: Client) -> list[str]:
    return [toast["message"] for toast in client.session.get(ToastMiddleware.CARRIED_TOASTS_SESSION_KEY, [])]


class TestMoneyFilter:
    @pytest.mark.parametrize(
        ("language", "expected"),
        [("en", "$42.50"), ("de", "42,50\N{NO-BREAK SPACE}€")],
    )
    def test_sign_placement_follows_the_language(self, language: str, expected: str) -> None:
        sign = "$" if language == "en" else "€"
        with translation.override(language):
            assert money("42.5", sign) == expected
