from django.utils.crypto import salted_hmac

from apps.core.pwa_constants import ANONYMOUS_SCOPE

_SCOPE_KEY_SALT = "apps.core.services.pwa_scope_service"
_SCOPE_LENGTH = 16


def resolve_scope(user) -> str:
    """Name the cache partition that the pages rendered for this visitor belong to.

    The service worker's caches live per origin, not per session. Without a partition the pages one
    account rendered stay readable offline once another account signs in on the same browser.

    Derived rather than the raw primary key: the value ends up in a cache name, and any script on
    the origin can enumerate those.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return ANONYMOUS_SCOPE

    return salted_hmac(_SCOPE_KEY_SALT, str(user.pk), algorithm="sha256").hexdigest()[:_SCOPE_LENGTH]
