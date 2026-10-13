import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.models import User
from apps.account.views import LogInUserView, UserForgotPasswordView
from apps.core.event_loop.messages.message import Message

pytestmark = pytest.mark.django_db


def test_get_regular(authenticated_client: Client) -> None:
    response = authenticated_client.get(reverse("account:forgot-password"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserForgotPasswordView.template_name
    assert "Forgot password" in response.content.decode()


def test_post_regular(authenticated_client: Client, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    recorded_messages = []

    def handle_message(message: Message) -> Message:
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", handle_message)
    response = authenticated_client.post(
        reverse("account:forgot-password"),
        data={"email": user.email},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert isinstance(recorded_messages[0], SendForgotPasswordEmail)

    assert response.template_name[0] == LogInUserView.template_name
    assert "Login" in response.content.decode()


def test_post_email_invalid(authenticated_client: Client) -> None:
    unknown_email = "unknown_email@local.local"
    response = authenticated_client.post(
        reverse("account:forgot-password"),
        data={"email": unknown_email},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserForgotPasswordView.template_name
    content = response.content.decode()
    # Rendered as an error, not just present somewhere on the page.
    assert "text-danger-text" in content
    assert unknown_email in content
    assert "is not registered with yamsa" in content
