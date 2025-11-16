from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse

PAYMENT_REMINDER_UNSUBSCRIBE_SALT = "payment-reminder-unsubscribe"


def build_payment_reminder_unsubscribe_url(user) -> str:
    signer = Signer(salt=PAYMENT_REMINDER_UNSUBSCRIBE_SALT)
    token = signer.sign(user.pk)
    backend = settings.BACKEND_URL.rstrip("/")
    return f"{backend}{reverse('account:payment-reminder-unsubscribe')}?token={token}"


def decode_payment_reminder_unsubscribe_token(token: str) -> int:
    signer = Signer(salt=PAYMENT_REMINDER_UNSUBSCRIBE_SALT)
    return int(signer.unsign(token))
