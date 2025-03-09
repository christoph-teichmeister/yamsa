"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import datetime
import logging
import os
import socket
import sys
from pathlib import Path

import environ
import sentry_sdk

env = environ.Env(
    SECRET_KEY=(str, ""),
    DJANGO_DEBUG=(bool, False),
    DJANGO_USE_DEBUG_TOOLBAR=(bool, False),
    DJANGO_DEBUG_TOOLBAR_USE_DOCKER=(bool, True),
    MAINTENANCE=(bool, False),
    PROJECT_BASE_URL=(str, ""),
    DJANGO_ADMIN_SUB_URL=(str, ""),
    # Webpush ENV
    VAPID_PUBLIC_KEY=(str, ""),
    VAPID_PRIVATE_KEY=(str, ""),
    VAPID_ADMIN_EMAIL=(str, ""),
    # Sentry ENV
    SENTRY_ENVIRONMENT=(str, "LOCAL"),
    SENTRY_DSN=(str, ""),
    # Database ENV
    DB_HOST=(str, ""),
    DB_NAME=(str, ""),
    DB_PASSWORD=(str, ""),
    DB_PORT=(str, ""),
    DB_USER=(str, ""),
    # Email ENV
    DJANGO_EMAIL_DEFAULT_FROM_EMAIL=(str, ""),
    DJANGO_EMAIL_BACKEND=(str, "django.core.mail.backends.smtp.EmailBackend"),
    DJANGO_EMAIL_HOST=(str, "yamsa_mailhog"),
    DJANGO_EMAIL_HOST_PASSWORD=(str, ""),
    DJANGO_EMAIL_HOST_USER=(str, ""),
    DJANGO_EMAIL_PORT=(int, 1025),
    DJANGO_EMAIL_URL=(environ.Env.email_url_config, "consolemail://"),
    DJANGO_EMAIL_USE_TLS=(bool, False),
    DJANGO_EMAIL_USE_SSL=(bool, False),
    # Cloudinary ENV
    CLOUDINARY_CLOUD_NAME=(str, ""),
    CLOUDINARY_API_KEY=(str, ""),
    CLOUDINARY_API_SECRET=(str, ""),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
CONFIG_DIR = Path(__file__).resolve().parent
APPS_DIR = CONFIG_DIR.parent
BASE_DIR = APPS_DIR.parent

PROJECT_BASE_URL = env("PROJECT_BASE_URL")
DJANGO_ADMIN_SUB_URL = env("DJANGO_ADMIN_SUB_URL")
LOGIN_URL = "/account/login/"

# Take environment variables from .env file
environ.Env.read_env(os.path.join(CONFIG_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DJANGO_DEBUG")

MAINTENANCE = env("MAINTENANCE")

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
vars().update(env.email_url("DJANGO_EMAIL_URL"))
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

EMAIL_HOST = env("DJANGO_EMAIL_HOST")
EMAIL_PORT = env("DJANGO_EMAIL_PORT")
EMAIL_USE_TLS = env("DJANGO_EMAIL_USE_TLS")
EMAIL_USE_SSL = env("DJANGO_EMAIL_USE_SSL")

EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD")

EMAIL_DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL = env("DJANGO_EMAIL_DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
EMAIL_DEFAULT_REPLY_TO_ADDRESS = env("DJANGO_EMAIL_DEFAULT_REPLY_TO_ADDRESS", default=EMAIL_DEFAULT_FROM_EMAIL)


IS_TESTING = False
if "test" in sys.argv or "test_coverage" in sys.argv:
    IS_TESTING = True


# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = (
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "account.User"

ALLOWED_HOSTS = ("*",)

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS += (RENDER_EXTERNAL_HOSTNAME,)

# Application definition

DJANGO_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
)

THIRD_PARTY_APPS = (
    "ambient_toolbox",
    "axes",
    "cloudinary",
    "cloudinary_storage",
    "django_extensions",
    "django_pony_express",
    "django_minify_html",
)

LOCAL_APPS = (
    "apps.account",
    "apps.currency",
    "apps.core",
    "apps.debt",
    "apps.mail",
    "apps.news",
    "apps.room",
    "apps.transaction",
    "apps.webpush",
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = (
    "django.middleware.gzip.GZipMiddleware",
    "django_minify_html.middleware.MinifyHtmlMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "ambient_toolbox.middleware.current_user.CurrentUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "apps.room.middleware.RoomToRequestMiddleware",
    "apps.core.middleware.maintenance_middleware.MaintenanceMiddleware",
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    "axes.middleware.AxesMiddleware",
)


if DEBUG:
    INSTALLED_APPS += ("django_browser_reload",)

    MIDDLEWARE = (
        "kolo.middleware.KoloMiddleware",
        *MIDDLEWARE,
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    )

    # WhiteNoise
    # ------------------------------------------------------------------------------
    # http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
    INSTALLED_APPS = ("whitenoise.runserver_nostatic", *INSTALLED_APPS)

    if env("DJANGO_USE_DEBUG_TOOLBAR"):
        # django-debug-toolbar
        # ------------------------------------------------------------------------------
        # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
        INSTALLED_APPS += ("debug_toolbar",)
        # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
        MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)
        # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
        DEBUG_TOOLBAR_CONFIG = {
            "DISABLE_PANELS": [
                "debug_toolbar.panels.redirects.RedirectsPanel",
                "debug_toolbar.panels.profiling.ProfilingPanel",
            ],
            "SHOW_TEMPLATE_CONTEXT": True,
        }
        # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
        INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
        if env("DJANGO_DEBUG_TOOLBAR_USE_DOCKER"):
            hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
            INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]


ROOT_URLCONF = "apps.config.urls"

TEMPLATES = (
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": (os.path.join(APPS_DIR, "templates"),),
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.account.context_processors.user_context",
                "apps.core.context_processors.core_context",
                "apps.currency.context_processors.currency_context",
                "apps.room.context_processors.room_context",
            ],
        },
    },
)

WSGI_APPLICATION = "apps.config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("DB_HOST"),
        "NAME": env("DB_NAME"),
        "PASSWORD": env("DB_PASSWORD"),
        "PORT": env("DB_PORT"),
        "USER": env("DB_USER"),
        "TEST": {
            "NAME": f"{env('DB_NAME')}_test",
        },
    }
}

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = (
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = (
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
)


# AXES
# ------------------------------------------------------------------------------
def axes_cooloff_time(request):
    return datetime.timedelta(0, LOGIN_TIMEDELTA)


LOGIN_TIMEDELTA = 15 * 60
LOGIN_COUNT = 3
AXES_COOLOFF_TIME = axes_cooloff_time
AXES_LOGIN_FAILURE_LIMIT = LOGIN_COUNT
AXES_USERNAME_FORM_FIELD = "username"  # TODO CT: "email" or "username"?
AXES_CLEANUP_DAYS = 30
# Block by Username only (i.e.: Same user different IP is still blocked, but different user same IP is not)
AXES_LOCKOUT_PARAMETERS = ["username"]  # TODO CT: "email" or "username"?
# Disable logging the IP-Address of failed login attempts by returning None for attempts to get the IP
# Ignore assigning a lambda function to a variable for brevity
AXES_CLIENT_IP_CALLABLE = lambda x: None  # noqa: E731
# Mask user-sensitive parameters in logging stream
AXES_SENSITIVE_PARAMETERS = ["username", "email", "ip_address"]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "CET"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# This setting tells Django at which URL static files are going to be served to the user.
# Here, they will be accessible at your-domain.onrender.com/static/...
STATIC_URL = "/static/"

# Tell Django to copy statics to the `staticfiles` directory in your application directory on Render.
STATICFILES_FOLDER = "static" if DEBUG else "staticfiles"
STATIC_ROOT = os.path.join(BASE_DIR, STATICFILES_FOLDER)

STATICFILES_DIRS = (os.path.join(APPS_DIR, "static"),)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Turn on WhiteNoise storage backend that takes care of compressing static files
        # and creating unique names for each version, so they can safely be cached forever.
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# media
MEDIA_URL = "/media/"
MEDIAFILES_FOLDER = "media" if DEBUG else "mediafiles"
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIAFILES_FOLDER)

if not DEBUG:
    STORAGES["default"]["BACKEND"] = "cloudinary_storage.storage.MediaCloudinaryStorage"
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": env("CLOUDINARY_API_KEY"),
        "API_SECRET": env("CLOUDINARY_API_SECRET"),
    }

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# PWA-related Settings
MANIFEST = {
    "background_color": "#2d2a2e",
    "categories": ["finance", "lifestyle", "productivity", "shopping", "utilities"],
    "description": "Yet another money split app",
    "dir": "auto",
    "display": "fullscreen",
    "display_override": ["window-controls-overlay", "fullscreen"],
    "edge_side_panel": {},
    "features": [],
    "icons": [
        {"src": "static/images/favicon.ico", "sizes": "48x48", "type": "image/ico"},
        {"src": "static/images/16x16.webp", "sizes": "16x16", "type": "image/webp"},
        {"src": "static/images/32x32.webp", "sizes": "32x32", "type": "image/webp"},
        {"src": "static/images/48x48.webp", "sizes": "48x48", "type": "image/webp"},
        {"src": "static/images/57x57-ios.webp", "sizes": "57x57", "type": "image/webp"},
        {"src": "static/images/60x60-ios.webp", "sizes": "60x60", "type": "image/webp"},
        {"src": "static/images/72x72-ios.webp", "sizes": "72x72", "type": "image/webp"},
        {"src": "static/images/76x76-ios.webp", "sizes": "76x76", "type": "image/webp"},
        {"src": "static/images/96x96.webp", "sizes": "96x96", "type": "image/webp"},
        {"src": "static/images/114x114-ios.webp", "sizes": "114x114", "type": "image/webp"},
        {"src": "static/images/120x120-ios.webp", "sizes": "120x120", "type": "image/webp"},
        {"src": "static/images/144x144.webp", "sizes": "144x144", "type": "image/webp"},
        {"src": "static/images/152x152-ios.webp", "sizes": "152x152", "type": "image/webp"},
        {"src": "static/images/180x180-ios.webp", "sizes": "180x180", "type": "image/webp"},
        {"src": "static/images/192x192.webp", "sizes": "192x192", "type": "image/webp"},
        {"src": "static/images/256x256.webp", "sizes": "256x256", "type": "image/webp"},
        {"src": "static/images/384x384.webp", "sizes": "384x384", "type": "image/webp"},
        {"src": "static/images/512x512.webp", "sizes": "512x512", "type": "image/webp"},
        {"src": "static/images/512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "static/images/512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
    "id": "yamsa",
    "lang": "en-US",
    "launch_handler": {"client_mode": ["navigate-existing", "auto"]},
    "name": "yamsa - Yet another money split app",
    "orientation": "any",
    "related_applications": [],
    "prefer_related_applications": False,
    "screenshots": [],
    "scope": "/",
    "short_name": "yamsa",
    "splash_screens": [],
    "start_url": "/",
    "theme_color": "#2d2a2e",
}

PWA_SERVICE_WORKER_DEBUG = DEBUG

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": env("VAPID_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": env("VAPID_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": env("VAPID_ADMIN_EMAIL"),
}
WEBPUSH_NOTIFICATION_CLASS = "apps.webpush.dataclasses.Notification"

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
        "django.security.cors": {
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
        "kolo": {
            "level": logging.WARNING,
            "handlers": ("console",),
        },
    },
}

# Sentry
if env("SENTRY_ENVIRONMENT") != "LOCAL":
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.1,
        environment=env("SENTRY_ENVIRONMENT"),
        integrations=[
            # DjangoIntegration(
            #     transaction_style="url",
            # ),
            # CeleryIntegration(),
        ],
    )

# Exclude main app from database serialization, speeds up tests, but removes ability to simulate rollbacks in tests
TEST_NON_SERIALIZED_APPS = ("apps",)

if IS_TESTING:
    base = environ.Path(__file__) - 1
    environ.Env.read_env(env_file=base("unittest.env"))

    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
    TEST_RUN = True
    WEBPUSH_NOTIFICATION_CLASS = "apps.webpush.dataclasses.TestNotification"

    # following settings will speed up the test runner:

    # Use a fast, insecure password hasher
    PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

    # Use in-memory cache and mail backend
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    }

    # We want templates to show useful errors even when DEBUG is set to False:
    TEMPLATES[0]["OPTIONS"]["debug"] = True

    MEDIA_URL = "http://media.testserver/"

    # Enable whitenoise autscanning
    WHITENOISE_AUTOREFRESH = True
