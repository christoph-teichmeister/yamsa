import socket

from django.utils.translation import gettext_lazy as _

from apps.config.settings.base import DEBUG, INSTALLED_APPS, MIDDLEWARE, env

# DEBUG
# ------------------------------------------------------------------------------
if DEBUG:
    INSTALLED_APPS += ("django_browser_reload", "django_extensions")

    MIDDLEWARE = (
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
            INTERNAL_IPS += [".".join([*ip.split(".")[:-1], "1"]) for ip in ips]
