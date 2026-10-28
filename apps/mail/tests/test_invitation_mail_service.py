from urllib.parse import parse_qs, urlparse

import pytest

from apps.account.models import User
from apps.account.utils.guest_registration_token import decode_guest_registration_token
from apps.mail.services.invitation_mail_service import InvitationEmailService


@pytest.mark.django_db
class TestInvitationEmailService:
    def test_link_is_urlencoded_and_carries_a_signed_guest_token(self, user: User, guest_user: User) -> None:
        tricky_email = "a+b&for_guest=1@local.local"
        service = InvitationEmailService(invited_by=user, recipient=guest_user, recipient_email_list=[tricky_email])

        query = parse_qs(urlparse(service.get_email_extra_context().cta_link).query)

        assert query["with_email"] == [tricky_email]
        assert "for_guest" not in query
        assert decode_guest_registration_token(query["guest_token"][0]) == guest_user.id
