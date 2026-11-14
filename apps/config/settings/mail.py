from apps.config.settings.base import env

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#mailers
_email_backend = env("DJANGO_EMAIL_BACKEND")
_email_host_user = env("DJANGO_EMAIL_HOST_USER")

MAILERS = {
    "default": {
        "BACKEND": _email_backend,
        # The console/locmem backends used for local dev and tests don't accept SMTP
        # options, so only pass them along when actually talking to a real SMTP server.
        "OPTIONS": (
            {
                "host": env("DJANGO_EMAIL_HOST"),
                "port": env("DJANGO_EMAIL_PORT"),
                "username": _email_host_user,
                "password": env("DJANGO_EMAIL_HOST_PASSWORD"),
                "use_tls": env("DJANGO_EMAIL_USE_TLS"),
                "use_ssl": env("DJANGO_EMAIL_USE_SSL"),
                # https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
                "timeout": 5,
            }
            if _email_backend == "django.core.mail.backends.smtp.EmailBackend"
            else {}
        ),
    },
}

EMAIL_DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL = env("DJANGO_EMAIL_DEFAULT_FROM_EMAIL", default=_email_host_user)
EMAIL_DEFAULT_REPLY_TO_ADDRESS = env("DJANGO_EMAIL_DEFAULT_REPLY_TO_ADDRESS", default=EMAIL_DEFAULT_FROM_EMAIL)
