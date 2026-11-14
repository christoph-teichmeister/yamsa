import datetime as dt

from django.http import HttpRequest
from django.utils.csp import CSP

from apps.config.settings.base import env

# SECURITY
# ------------------------------------------------------------------------------
# Number of reverse proxies in front of the app that append to X-Forwarded-For (see apps.core.utils.get_client_ip).
# 0 ignores the header and uses REMOTE_ADDR. Behind a proxy that makes every client share the proxy's address, so
# production must set the real hop count; a value larger than the real one lets clients spoof their IP.
TRUSTED_PROXY_COUNT = env("DJANGO_TRUSTED_PROXY_COUNT")
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
# Use X-Forwarded-Proto Header to determine SSL status (useful for API docs)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# The TLS-terminating proxy owns the HTTP->HTTPS redirect; redirecting here too would loop on plain-HTTP
# health checks. HSTS is opt-in per environment through DJANGO_SECURE_HSTS_SECONDS (below).
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE = env("DJANGO_SESSION_COOKIE_SECURE")
SECURE_CONTENT_TYPE_NOSNIFF = True

# https://docs.djangoproject.com/en/5.1/ref/settings/#silenced-system-checks
SILENCED_SYSTEM_CHECKS = ()

# https://docs.djangoproject.com/en/5.1/ref/settings/#secure-hsts-seconds
SECURE_HSTS_SECONDS = env("DJANGO_SECURE_HSTS_SECONDS")
if SECURE_HSTS_SECONDS > 0:
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Content Security Policy support was added in Django 6.0.
# https://docs.djangoproject.com/en/6.0/releases/6.0/#content-security-policy-support
# Allow only nonce-backed inline scripts while keeping inline styles open for legacy attributes.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, "https:", "'unsafe-inline'"],
    "img-src": [CSP.SELF, "data:", "https:"],
    "font-src": [CSP.SELF, "https:"],
    "connect-src": [CSP.SELF, "https:"],
    "frame-ancestors": [CSP.SELF],
    "base-uri": [CSP.SELF],
    "object-src": [CSP.NONE],
}

# Set URLs and URL-Protocol for CORS and CSRF settings
FRONTEND_URL = env("DJANGO_FRONTEND_URL")
BACKEND_URL = env("DJANGO_BACKEND_URL")
INACTIVITY_REMINDER_ENABLED = env("DJANGO_INACTIVITY_REMINDER_ENABLED")
INACTIVITY_REMINDER_DAYS = env("DJANGO_INACTIVITY_REMINDER_DAYS")
URL_PROTOCOL = "https://" if SESSION_COOKIE_SECURE else "http://"


# SESSION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#sessions

# Set the default session cookie age to 48 hours (172800 seconds)
SESSION_COOKIE_AGE = 60 * 60 * 48
DJANGO_REMEMBER_ME_SESSION_AGE = env("DJANGO_REMEMBER_ME_SESSION_AGE")
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# https://docs.djangoproject.com/en/dev/ref/settings/#std-setting-SECURE_REFERRER_POLICY
SECURE_REFERRER_POLICY = "same-origin"

# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = (FRONTEND_URL, BACKEND_URL)


# AXES
# ------------------------------------------------------------------------------
def axes_cooloff_time(request: HttpRequest) -> dt.timedelta:
    return dt.timedelta(0, LOGIN_TIMEDELTA)


LOGIN_TIMEDELTA = 15 * 60
LOGIN_COUNT = 3
AXES_COOLOFF_TIME = axes_cooloff_time
AXES_LOGIN_FAILURE_LIMIT = LOGIN_COUNT
AXES_USERNAME_FORM_FIELD = "email"  # use the email field from the login form
# Axes maps the email login form field (AXES_USERNAME_FORM_FIELD) into the "username"
# slot before applying lockouts, so AXES_LOCKOUT_PARAMETERS now contains a single entry that pairs
# "username" and "ip_address" to key attempts per user/IP combination.
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
# Axes and the forgot-password limit share one client-IP resolver (django-ipware is not installed, so Axes would
# otherwise only ever see REMOTE_ADDR, i.e. the proxy).
# Keep sensitive parameters masked via AXES_SENSITIVE_PARAMETERS.
AXES_CLIENT_IP_CALLABLE = "apps.core.utils.get_client_ip"
# Mask user-sensitive parameters in logging stream
AXES_SENSITIVE_PARAMETERS = ["username", "email", "ip_address"]


# PASSKEYS
# ------------------------------------------------------------------------------
def _passkey_rp_id(request: HttpRequest | None = None) -> str:
    from urllib.parse import urlparse

    return urlparse(BACKEND_URL).hostname or "localhost"


FIDO_SERVER_ID = _passkey_rp_id
FIDO_SERVER_NAME = "yamsa"
# Read by django-passkeys (no authenticator-attachment restriction); not referenced in our own code.
KEY_ATTACHMENT = None
