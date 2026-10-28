from django.core.signing import BadSignature, TimestampSigner

GUEST_REGISTRATION_SALT = "guest-registration"
GUEST_REGISTRATION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


def build_guest_registration_token(guest_id: int) -> str:
    return TimestampSigner(salt=GUEST_REGISTRATION_SALT).sign(str(guest_id))


def decode_guest_registration_token(token: str | None) -> int | None:
    """Return the guest id a valid, unexpired invitation token was issued for, else None."""
    if not token:
        return None
    try:
        value = TimestampSigner(salt=GUEST_REGISTRATION_SALT).unsign(token, max_age=GUEST_REGISTRATION_MAX_AGE_SECONDS)
        return int(value)
    except (BadSignature, ValueError):
        return None
