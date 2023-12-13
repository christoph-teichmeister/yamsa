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
    # Database ENV
    DB_HOST=(str, ""),
    DB_NAME=(str, ""),
    DB_PASSWORD=(str, ""),
    DB_PORT=(str, ""),
    DB_USER=(str, ""),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
CONFIG_DIR = Path(__file__).resolve().parent
APPS_DIR = CONFIG_DIR.parent
BASE_DIR = APPS_DIR.parent

PROJECT_BASE_URL = env("PROJECT_BASE_URL")
DJANGO_ADMIN_SUB_URL = env("DJANGO_ADMIN_SUB_URL")

# Take environment variables from .env file
environ.Env.read_env(os.path.join(CONFIG_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

MAINTENANCE = env("MAINTENANCE")

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
    "django_browser_reload",
    "django_extensions",
)

LOCAL_APPS = (
    "apps.account",
    "apps.currency",
    "apps.core",
    "apps.debt",
    "apps.news",
    "apps.room",
    "apps.transaction",
    "apps.webpush",
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = (
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
STATICFILES_FOLDER = f"{'staticfiles' if DEBUG else 'static'}"
STATIC_ROOT = os.path.join(BASE_DIR, STATICFILES_FOLDER)

# Turn on WhiteNoise storage backend that takes care of compressing static files
# and creating unique names for each version, so they can safely be cached forever.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = (os.path.join(APPS_DIR, "static"),)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# PWA-related Settings
MANIFEST = {
    "name": "yamsa - Yet another money split app",
    "short_name": "yamsa",
    "description": "Yet another money split app",
    "dir": "auto",
    "lang": "en-US",
    "display": "standalone",
    "orientation": "any",
    "start_url": "/",
    "scope": "/",
    "background_color": "#2d2a2e",
    "theme_color": "#2d2a2e",
    "icons": [
        {"src": "static/images/favicon.ico", "sizes": "48x48", "type": "image/ico"},
        {"src": "static/images/favicon-16x16.png", "sizes": "16x16", "type": "image/png"},
        {"src": "static/images/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
        {"src": "static/images/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
        {"src": "static/images/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "static/images/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"},
    ],
    "splash_screens": [],
}

PWA_SERVICE_WORKER_DEBUG = DEBUG

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": env("VAPID_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": env("VAPID_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": env("VAPID_ADMIN_EMAIL"),
}


if IS_TESTING:
    # DEBUG = False
    # EMAIL_URL = "memorymail://"
    # CACHE_BACKEND = "local"
    # EMAIL_BACKEND = "memorymail://"
    # PYTHONUNBUFFERED = 0
    TEST_RUN = True
