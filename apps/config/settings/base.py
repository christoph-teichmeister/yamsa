import contextlib
import logging
import socket
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
CONFIG_DIR = Path(__file__).resolve().parent.parent  # apps/config, which holds .env and unittest.env
APPS_DIR = CONFIG_DIR.parent
BASE_DIR = APPS_DIR.parent

env = environ.Env(
    DJANGO_ADMIN_URL=(str, "admin"),
    DJANGO_ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    DJANGO_BACKEND_URL=(str, "http://localhost:8002"),
    DJANGO_CACHE_URL=(str, "locmemcache://"),
    DJANGO_DATABASE_URL=(str, "sqlite:///sqlite.db"),
    DJANGO_DEBUG=(bool, False),
    DJANGO_DEBUG_TOOLBAR_USE_DOCKER=(bool, True),
    DJANGO_FRONTEND_URL=(str, "http://localhost:8002"),
    DJANGO_SECRET_KEY=(str, ""),
    DJANGO_SECURE_HSTS_SECONDS=(int, 0),
    DJANGO_TRUSTED_PROXY_COUNT=(int, 0),
    DJANGO_SESSION_COOKIE_SECURE=(bool, True),
    DJANGO_REMEMBER_ME_SESSION_AGE=(int, 60 * 60 * 24 * 30),  # 30 days
    DJANGO_USE_DEBUG_TOOLBAR=(bool, False),
    E2E_TESTING=(bool, False),
    MAINTENANCE=(bool, False),
    # Cloudinary ENV
    CLOUDINARY_CLOUD_NAME=(str, ""),
    CLOUDINARY_API_KEY=(str, ""),
    CLOUDINARY_API_SECRET=(str, ""),
    # Email ENV
    DJANGO_EMAIL_DEFAULT_FROM_EMAIL=(str, ""),
    DJANGO_EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    DJANGO_EMAIL_HOST=(str, "yamsa_mailhog"),
    DJANGO_EMAIL_HOST_PASSWORD=(str, ""),
    DJANGO_EMAIL_HOST_USER=(str, ""),
    DJANGO_EMAIL_PORT=(int, 1027),
    DJANGO_EMAIL_USE_TLS=(bool, False),
    DJANGO_EMAIL_USE_SSL=(bool, False),
    DJANGO_INACTIVITY_REMINDER_ENABLED=(bool, True),
    DJANGO_INACTIVITY_REMINDER_DAYS=(int, 30),
    # Sentry ENV
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, "local"),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.1),
    SENTRY_LOG_LEVEL=(int, logging.INFO),
    # Render sets this itself on every deploy of a git-backed service, in the build and in the
    # runtime environment. Nothing has to be configured by hand for it to be there.
    RENDER_GIT_COMMIT=(str, ""),
    # Webpush ENV
    VAPID_PUBLIC_KEY=(str, ""),
    VAPID_PRIVATE_KEY=(str, ""),
    VAPID_ADMIN_EMAIL=(str, ""),
)

# Take environment variables from .env file
environ.Env.read_env(CONFIG_DIR / ".env")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DJANGO_DEBUG")

# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Europe/Berlin"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en"
# https://docs.djangoproject.com/en/dev/ref/settings/#languages
LANGUAGES = (
    ("en", _("English")),
    ("de", _("German")),
)
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = (f"{APPS_DIR}/locale",)
# https://docs.djangoproject.com/en/dev/topics/i18n/formatting/#creating-custom-format-files
FORMAT_MODULE_PATH = [
    "apps.core.formats",
]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DJANGO_DATABASE_URL")}

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "apps.config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "apps.config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
)

THIRD_PARTY_APPS = (
    "ambient_toolbox",
    "axes",
    "cloudinary",
    "cloudinary_storage",
    "django_minify_html",
    "django_pony_express",
    "passkeys",
    "webpack_loader",
)

LOCAL_APPS = (
    "apps.account",
    "apps.currency",
    "apps.core",
    "apps.debt",
    "apps.importer",
    "apps.mail",
    "apps.news",
    "apps.room",
    "apps.transaction",
    "apps.webpush",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = (
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    "apps.account.backends.YamsaPasskeyBackend",
    "django.contrib.auth.backends.ModelBackend",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "account.User"

# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "account:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account:login"

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

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Minify HTML before GZipping for a clearer processing flow
    "django.middleware.gzip.GZipMiddleware",
    "django_minify_html.middleware.MinifyHtmlMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.session_keep_alive_middleware.SessionKeepAliveMiddleware",
    "ambient_toolbox.middleware.current_request.CurrentRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.room.middleware.RoomToRequestMiddleware",
    "apps.core.middleware.maintenance_middleware.MaintenanceMiddleware",
    "apps.core.middleware.toast_middleware.ToastMiddleware",
    "apps.core.middleware.pwa_scope_middleware.PwaScopeHeaderMiddleware",
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    "axes.middleware.AxesMiddleware",
)


# STORAGES
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Turn on WhiteNoise storage backend that takes care of compressing static files
        # and creating unique names for each version, so they can safely be cached forever.
        # Custom subclass because django-passkeys (still as of 2.1) ships bootstrap-toggle.min.js without its
        # .map file; plain CompressedManifestStaticFilesStorage would abort collectstatic on that reference.
        "BACKEND": "apps.config.storage.ManifestStaticFilesStorage",
    },
}

# STATIC (CSS, JavaScript, Images)  # noqa: ERA001 - section header, not commented-out code
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/howto/static-files/

# This setting tells Django at which URL static files are going to be served to the user.
# Here, they will be accessible at your-domain.onrender.com/static/...
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# Tell Django to copy statics to the `staticfiles` directory in your application directory on Render.
STATICFILES_FOLDER = "static" if DEBUG else "staticfiles"
STATIC_ROOT = BASE_DIR / STATICFILES_FOLDER

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
# The second entry is webpack's own output (webpack.config.js), deliberately outside apps/ - see
# the comment on that config's bundlesPath. Its "bundles" subfolder lands at the same /static/
# URL as before, since FileSystemFinder maps a STATICFILES_DIRS entry's contents straight under
# STATIC_URL regardless of the entry's own path.
STATICFILES_DIRS = (
    APPS_DIR / "static",
    BASE_DIR / "webpack_bundles",
)
STATICFILES_FINDERS = (
    # Default finders
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "bundles/",
        "STATS_FILE": BASE_DIR / "webpack_bundles" / "bundles" / "webpack-stats.json",
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update.js"],
        "LOADER_CLASS": "apps.config.custom_webpack_loader.NormalizedWebpackLoader",
        "CACHE": not DEBUG,
    }
}

# MEDIA
# ------------------------------------------------------------------------------
MEDIAFILES_FOLDER = "media" if DEBUG else "mediafiles"
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = BASE_DIR / MEDIAFILES_FOLDER
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

if env("CLOUDINARY_API_KEY"):
    STORAGES["default"]["BACKEND"] = "cloudinary_storage.storage.MediaCloudinaryStorage"
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": env("CLOUDINARY_API_KEY"),
        "API_SECRET": env("CLOUDINARY_API_SECRET"),
    }

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = (
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": (
            f"{APPS_DIR}/templates",
            f"{BASE_DIR}/templates",
        ),
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": (
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.csp",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "apps.account.context_processors.user_context",
                "apps.core.context_processors.core_context",
                "apps.currency.context_processors.currency_context",
                "apps.room.context_processors.room_context",
            ),
            "builtins": [
                "apps.room.templatetags.room_tags",
                # 46 templates draw an icon; a `{% load %}` in each of them would be 46 lines
                # saying the same thing, and one missing line is a TemplateSyntaxError.
                "apps.core.templatetags.icon_tags",
            ],
        },
    },
)

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = env("DJANGO_ADMIN_URL")
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = ("christoph.teichmeister@gmail.com",)
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# https://cookiecutter-django.readthedocs.io/en/latest/settings.html#other-environment-settings

# ALLOWED_HOSTS
# ------------------------------------------------------------------------------
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Container-internal IP lets healthchecks pass without a Host header; the hostname may not resolve outside Docker.
with contextlib.suppress(OSError):
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, socket.gethostbyname(socket.gethostname())]

# CACHES
# ------------------------------------------------------------------------------
CACHES = {"default": env.cache("DJANGO_CACHE_URL")}
