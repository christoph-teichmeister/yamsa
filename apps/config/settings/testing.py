import sys

import environ

from apps.config.settings.base import (
    BASE_DIR,
    CONFIG_DIR,
    DATABASES,
    MEDIA_URL,
    PASSWORD_HASHERS,
    STORAGES,
    WEBPACK_LOADER,
    env,
)
from apps.config.settings.integrations import WEBPUSH_NOTIFICATION_CLASS
from apps.config.settings.mail import MAILERS

# TESTING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/5.1/ref/settings/#test-non-serialized-apps
# Exclude main app from database serialization, speeds up tests, but removes ability to simulate rollbacks in tests
TEST_NON_SERIALIZED_APPS = ("apps",)

E2E_TESTING = env.bool("E2E_TESTING", default=False)

if env.bool("DJANGO_TESTING", False) or any(keyword in sys.argv for keyword in ("test", "test_coverage")):
    environ.Env.read_env(env_file=CONFIG_DIR / "unittest.env")

    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
    if E2E_TESTING:
        # pytest-django hands an in-memory SQLite database to the live server as one connection
        # shared by every request thread, so two requests a page fires at once (a form post
        # beside /pwa/session/ or a service-worker warm-up) collide and fail with "database table
        # is locked" - a 500, or a 400 when it hits the session save. A file gives each thread
        # its own connection; WAL lets reads run beside a write, and IMMEDIATE takes the write
        # lock when a transaction opens, so a writer waits out the timeout instead of failing.
        DATABASES["default"]["TEST"] = {"NAME": str(BASE_DIR / "e2e-test.sqlite3")}
        DATABASES["default"]["OPTIONS"] = {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",
            "init_command": "PRAGMA journal_mode=WAL;",
        }
    TEST_RUN = True
    WEBPUSH_NOTIFICATION_CLASS = "apps.webpush.dataclasses.TestNotification"

    # following settings will speed up the test runner:

    # Use a fast, insecure password hasher
    PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

    # Use in-memory cache and mail backend
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    }

    MEDIA_URL = "http://media.testserver/"

    # Enable whitenoise autscanning
    WHITENOISE_AUTOREFRESH = True

    # Use simple storage in tests — no manifest required, avoids issues with newly added app
    # static files that haven't been collected yet. This also lets Playwright e2e tests resolve
    # {% static %} URLs straight through STATICFILES_DIRS/finders (incl. the webpack bundle
    # `yarn build` writes there) without a `collectstatic` run: live_server always serves static
    # files via StaticFilesHandler+finders, which only know unhashed filenames, so a manifest
    # storage here would 404 on every hashed URL it emits.
    STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

    if not E2E_TESTING:
        WEBPACK_LOADER["DEFAULT"].update(
            {
                "LOADER_CLASS": "webpack_loader.loaders.FakeWebpackLoader",
                "CACHE": False,
            }
        )
