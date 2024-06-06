"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
import sys
from pathlib import Path

import environ
import sentry_sdk

env = environ.Env(
    SECRET_KEY=(str, ""),
    DEBUG=(bool, False),
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
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
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
IS_LOCALHOST = "localhost" in PROJECT_BASE_URL
DJANGO_ADMIN_SUB_URL = env("DJANGO_ADMIN_SUB_URL")
LOGIN_URL = "/account/login/"

# Take environment variables from .env file
environ.Env.read_env(os.path.join(CONFIG_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

MAINTENANCE = env("MAINTENANCE")

# E-Mail Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = 587
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = f"{BASE_DIR}/tmp/emails"


IS_TESTING = False
if "test" in sys.argv or "test_coverage" in sys.argv:
    IS_TESTING = True

if IS_TESTING:
    base = environ.Path(__file__) - 1
    environ.Env.read_env(env_file=base("unittest.env"))

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
    "cloudinary",
    "cloudinary_storage",
    "django_browser_reload",
    "django_extensions",
    "django_pony_express",
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
    "kolo.middleware.KoloMiddleware",
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
)

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
            "NAME": f'{env("DB_NAME")}_test',
        },
    }
}

if IS_TESTING:
    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = (
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
)

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

if env("SENTRY_ENVIRONMENT") != "LOCAL":
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        environment=env("SENTRY_ENVIRONMENT"),
        integrations=[
            # DjangoIntegration(
            #     transaction_style="url",
            # ),
            # CeleryIntegration(),
        ],
    )

if IS_TESTING:
    # DEBUG = False
    # EMAIL_URL = "memorymail://"
    # CACHE_BACKEND = "local"
    # EMAIL_BACKEND = "memorymail://"
    # PYTHONUNBUFFERED = 0
    TEST_RUN = True
    WEBPUSH_NOTIFICATION_CLASS = "apps.webpush.dataclasses.TestNotification"
