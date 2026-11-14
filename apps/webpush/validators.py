import ipaddress
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

_INTERNAL_HOST_SUFFIXES = (".local", ".localhost", ".internal", ".lan", ".home.arpa")


def is_safe_push_endpoint(endpoint: str) -> bool:
    """True for an https URL whose host is not loopback, private, link-local or otherwise internal.

    The server POSTs to this URL on every push, so a stored endpoint is an SSRF vector.
    ponytail: host names are judged by their text only; a public name that resolves to a private
    address (DNS rebinding) still passes. Resolve and pin the address at send time if that matters.
    """
    try:
        parts = urlsplit(endpoint)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return False

    if parts.scheme != "https" or not host:
        return False

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "." in host and not host.endswith(_INTERNAL_HOST_SUFFIXES)

    return address.is_global


def validate_push_endpoint(endpoint: str) -> None:
    if not is_safe_push_endpoint(endpoint):
        raise ValidationError(_("The push endpoint must be a public https URL."), code="unsafe_push_endpoint")
