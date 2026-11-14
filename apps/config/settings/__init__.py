"""Django settings for the yamsa project (DJANGO_SETTINGS_MODULE=apps.config.settings).

The submodules are star-imported in this order, and the order is load-bearing: `testing` reads
unittest.env into os.environ, which only affects `env()` calls made after it (the `debug` block), and
`testing` and `debug` rebind or extend names that earlier modules defined.
"""
# ruff: noqa: F403 - the package is the settings namespace, so every public name of each part is re-exported

# isort: off
from apps.config.settings.base import *
from apps.config.settings.security import *
from apps.config.settings.logs import *
from apps.config.settings.mail import *
from apps.config.settings.pwa import *
from apps.config.settings.integrations import *
from apps.config.settings.testing import *
from apps.config.settings.debug import *
# isort: on
