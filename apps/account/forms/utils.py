from django.core.exceptions import ValidationError

from apps.account.models import User


def validate_unique_email(email: str, *, error_message: str, exclude_user_id: int | None = None) -> str:
    """Normalize the email and ensure it is not already taken."""
    normalized_email = User.objects.normalize_email(email) or email
    query = User.objects.filter(email__iexact=normalized_email)
    if exclude_user_id is not None:
        query = query.exclude(id=exclude_user_id)
    if query.exists():
        raise ValidationError(error_message.format(email=normalized_email))

    return normalized_email
