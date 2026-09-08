import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# The profile field is offered as a bare handle behind a static "@", but people paste what they
# have: a full profile URL, an "@name", a link with PayPal's locale query. Every one of those ends
# up inside the payment URL verbatim and turns it into a 404, so they are stripped before storing.
_PAYPAL_URL_PREFIX_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?paypal(?:\.me/|\.com/paypalme/)",
    flags=re.IGNORECASE,
)

# PayPal.Me handles are alphanumeric and at most 20 characters. Anything else cannot resolve to a
# profile, so it is rejected rather than stored as a link that is broken on arrival.
_PAYPAL_ME_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9]{1,20}$")

PAYPAL_ME_USERNAME_ERROR_MESSAGE = _("Enter your PayPal.Me username - letters and numbers only, at most 20 characters.")


def normalize_paypal_me_username(value: str | None) -> str | None:
    """Reduce anything paste-shaped to the bare PayPal.Me handle, or raise if it cannot be one."""
    if value is None:
        return None

    normalized_value = value.strip()
    normalized_value = _PAYPAL_URL_PREFIX_PATTERN.sub("", normalized_value)
    # A pasted link carries PayPal's own locale query, and a prefilled amount would sit in the path.
    normalized_value = re.split(r"[?#/]", normalized_value, maxsplit=1)[0]
    normalized_value = normalized_value.strip().lstrip("@").strip()

    if not normalized_value:
        # Clearing the field is how a user opts out of the PayPal button, so blank stays blank.
        return None

    if not _PAYPAL_ME_USERNAME_PATTERN.match(normalized_value):
        raise ValidationError(PAYPAL_ME_USERNAME_ERROR_MESSAGE)

    return normalized_value
