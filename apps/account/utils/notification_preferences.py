from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse

PAYMENT_REMINDER_UNSUBSCRIBE_SALT = "payment-reminder-unsubscribe"
PAYMENT_REMINDER_VARIANT = "payment"
ROOM_REMINDER_VARIANT = "room"
_VALID_REMINDER_VARIANTS = {PAYMENT_REMINDER_VARIANT, ROOM_REMINDER_VARIANT}


def normalize_reminder_variant(variant: str | None) -> str:
    normalized_variant = (variant or "").strip().lower()
    if normalized_variant in _VALID_REMINDER_VARIANTS:
        return normalized_variant
    return PAYMENT_REMINDER_VARIANT


def build_payment_reminder_unsubscribe_url(user, *, variant: str | None = None) -> str:
    signer = Signer(salt=PAYMENT_REMINDER_UNSUBSCRIBE_SALT)
    token = signer.sign(user.pk)
    backend = settings.BACKEND_URL.rstrip("/")
    normalized_variant = normalize_reminder_variant(variant)
    return f"{backend}{reverse('account:payment-reminder-unsubscribe')}?token={token}&variant={normalized_variant}"


def decode_payment_reminder_unsubscribe_token(token: str) -> int:
    signer = Signer(salt=PAYMENT_REMINDER_UNSUBSCRIBE_SALT)
    return int(signer.unsign(token))
