import importlib

import pytest
from django.conf import settings

SETTINGS_PARTS = ("base", "security", "logs", "mail", "pwa", "integrations", "testing", "debug")


class TestSettingsPackage:
    @pytest.mark.parametrize("part", SETTINGS_PARTS)
    def test_every_part_is_importable(self, part: str) -> None:
        importlib.import_module(f"apps.config.settings.{part}")

    def test_dotenv_files_are_looked_up_next_to_the_package(self) -> None:
        assert settings.CONFIG_DIR == settings.APPS_DIR / "config"
        assert settings.APPS_DIR.parent == settings.BASE_DIR

    def test_testing_overrides_win_over_base_values(self) -> None:
        assert settings.PASSWORD_HASHERS == ("django.contrib.auth.hashers.MD5PasswordHasher",)
        assert settings.WEBPUSH_NOTIFICATION_CLASS == "apps.webpush.dataclasses.TestNotification"
        assert settings.MAILERS["default"]["BACKEND"] == "django.core.mail.backends.locmem.EmailBackend"
