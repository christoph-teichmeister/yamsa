from django.core.exceptions import ValidationError

from apps.account.models import User


def validate_unique_email(email: str, *, error_message: str) -> str:
    """Normalize the email and ensure it is not already taken."""
    normalized_email = User.objects.normalize_email(email) or email
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise ValidationError(error_message.format(email=normalized_email))

    return normalized_email
