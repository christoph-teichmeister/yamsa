import http

import pytest
from django.urls import reverse

from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.views import GuestSendInvitationEmailView, UserListForRoomView

pytestmark = pytest.mark.django_db


@pytest.fixture
def guest_send_invitation_url(room, guest_user):
    return reverse(
        "account:guest-send-invitation-email",
        kwargs={"room_slug": room.slug, "pk": guest_user.id},
    )


def test_get_regular(authenticated_client, guest_user, room, guest_send_invitation_url):
    response = authenticated_client.get(guest_send_invitation_url)

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == GuestSendInvitationEmailView.template_name
    assert f'Invite {guest_user.name} to "{room.name}"' in response.content.decode()
    assert response.context_data["active_tab"] == "people"


def test_post_regular(authenticated_client, guest_send_invitation_url, monkeypatch):
    recorded_messages = []

    def handle_message(message):
        recorded_messages.append(message)
        return message

    monkeypatch.setattr(
        "apps.account.views.guest_send_invitation_email_view.handle_message",
        handle_message,
    )
    response = authenticated_client.post(
        guest_send_invitation_url,
        data={"email": "some_email@local.local"},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert isinstance(recorded_messages[0], SendInvitationEmail)

    assert response.template_name[0] == UserListForRoomView.template_name
    content = response.content.decode()
    assert "Room roster" in content
    assert "Add guest" in content
    assert response.context_data["active_tab"] == "people"


def test_post_email_invalid(authenticated_client, guest_send_invitation_url):
    response = authenticated_client.post(
        guest_send_invitation_url,
        data={"email": "invalid_email_format"},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == GuestSendInvitationEmailView.template_name
    assert "Enter a valid email address." in response.content.decode()
    assert response.context_data["active_tab"] == "people"
