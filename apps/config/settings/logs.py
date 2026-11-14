import logging
import os

from apps.config.settings.base import DEBUG, env
from apps.config.settings.security import BACKEND_URL

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
DJANGO_LOG_LEVEL = logging.INFO if DEBUG else logging.ERROR

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose-3": {
            "format": "%(levelname)s | %(asctime)s | pid: %(process)d | thread: %(thread)d | %(module)s > %(message)s",
        },
        "verbose-2": {
            "format": "%(levelname)s | %(asctime)s | %(module)s > %(message)s",
        },
        "simple": {
            "format": "%(levelname)s | %(asctime)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": logging.DEBUG,
            "class": "logging.StreamHandler",
            "formatter": "verbose-2",
        },
    },
    "root": {
        "level": logging.INFO,
        "handlers": ("console",),
    },
    "loggers": {
        "django": {
            "handlers": ("console",),
            "level": DJANGO_LOG_LEVEL,
            "propagate": True,
        },
        "django.db.backends": {
            "level": logging.WARNING,
            "handlers": ("console",),
            "propagate": False,
        },
        "django.utils.autoreload": {
            "level": DJANGO_LOG_LEVEL,
            "handlers": ("console",),
            "propagate": False,
        },
        "django.server": {
            "level": logging.WARNING,
            "handlers": ("console",),
            "propagate": False,
        },
        "django.security.DisallowedHost": {
            "level": logging.WARNING,
            "handlers": ("console",),
            "propagate": False,
        },
        "django.security.csrf": {
            "handlers": ("console",),
            "level": logging.WARNING,
        },
        "axes": {
            "handlers": ("console",),
            "level": logging.WARNING,
        },
        "django_pony_express": {
            "handlers": ("console",),
            "level": logging.INFO,
            "propagate": True,
        },
        "fontTools": {
            "handlers": ("console",),
            "level": logging.WARNING,
        },
        "fontTools.subset": {
            "handlers": ("console",),
            "level": logging.WARNING,
        },
        "fontTools.ttLib.ttFont": {
            "handlers": ("console",),
            "level": logging.WARNING,
        },
        # Errors logged by the SDK itself
        "sentry_sdk": {
            "level": logging.WARNING,
            "handlers": ("console",),
            "propagate": False,
        },
    },
}

# RELEASE
# ------------------------------------------------------------------------------
# Which build is running. Sentry groups issues by it and the service worker names its caches after
# it, so a value that does not move between deploys is wrong in both places at once - stale caches
# on every device, and every issue filed against the same version.
#
# Render sets RENDER_GIT_COMMIT itself on every deploy of a git-backed service, in the build and in
# the runtime environment, so this needs nothing configured to be right. Deliberately the only
# source: a second one would have to be kept in step with this by hand.
#
# Somewhere without it - a Docker deploy, a working copy - this is empty. Sentry then falls back to
# its own reading of the SENTRY_RELEASE environment variable (sentry_sdk.utils.get_default_release),
# and the service worker to a fingerprint of the asset manifests.
RELEASE = env("RENDER_GIT_COMMIT")

# SENTRY
# ------------------------------------------------------------------------------
if os.environ.get("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        integrations=(
            sentry_logging,
            DjangoIntegration(),
        ),
        max_breadcrumbs=50,
        debug=False,
        # None, not "": an empty string is a release named "" to the SDK, where None lets it fall
        # back to its own detection.
        release=RELEASE or None,
        environment=env("SENTRY_ENVIRONMENT"),
        server_name=BACKEND_URL,
        send_default_pii=True,
        traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE"),
    )
