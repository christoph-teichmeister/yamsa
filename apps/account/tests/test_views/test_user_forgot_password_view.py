import http

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.account.views import LogInUserView, UserForgotPasswordView
from apps.core.event_loop.messages.message import Message

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_throttle_cache() -> None:
    cache.clear()


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


def test_post_unknown_email_gives_the_same_answer_and_sends_nothing(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded_messages = []
    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", recorded_messages.append)

    response = client.post(reverse("account:forgot-password"), data={"email": "unknown_email@local.local"})

    assert response.status_code == http.HTTPStatus.FOUND
    assert response["Location"] == reverse("account:login")
    assert not recorded_messages


def test_post_does_not_change_the_password(client: Client, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", lambda message: message)
    password_before = user.password

    client.post(reverse("account:forgot-password"), data={"email": user.email})

    user.refresh_from_db()
    assert user.password == password_before


def test_post_is_throttled_per_email(client: Client, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    recorded_messages = []
    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", recorded_messages.append)

    for email in (user.email, user.email.upper()):
        response = client.post(reverse("account:forgot-password"), data={"email": email})
        assert response.status_code == http.HTTPStatus.FOUND

    assert len(recorded_messages) == 1


def test_post_with_duplicate_email_does_not_crash(client: Client, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    UserFactory(email=user.email.upper())
    recorded_messages = []
    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", recorded_messages.append)

    response = client.post(reverse("account:forgot-password"), data={"email": user.email})

    assert response.status_code == http.HTTPStatus.FOUND
    assert len(recorded_messages) == 2


def test_post_for_guest_sends_nothing(client: Client, guest_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    recorded_messages = []
    monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", recorded_messages.append)

    client.post(reverse("account:forgot-password"), data={"email": guest_user.email})

    assert not recorded_messages


def _reset_url(user: User, token: str | None = None) -> str:
    return reverse(
        "account:reset-password",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token or default_token_generator.make_token(user),
        },
    )


def test_reset_with_valid_link_sets_new_password(client: Client, user: User) -> None:
    url = _reset_url(user)

    assert client.get(url).status_code == http.HTTPStatus.OK
    response = client.post(url, data={"new_password1": "Brand-new-pw-93!", "new_password2": "Brand-new-pw-93!"})

    assert response.status_code == http.HTTPStatus.FOUND
    assert response["Location"] == reverse("account:login")
    user.refresh_from_db()
    assert user.check_password("Brand-new-pw-93!")


def test_reset_link_works_only_once(client: Client, user: User) -> None:
    url = _reset_url(user)
    client.post(url, data={"new_password1": "Brand-new-pw-93!", "new_password2": "Brand-new-pw-93!"})

    response = client.post(url, data={"new_password1": "Other-new-pw-94!", "new_password2": "Other-new-pw-94!"})

    assert response.status_code == http.HTTPStatus.FOUND
    assert response["Location"] == reverse("account:forgot-password")
    user.refresh_from_db()
    assert user.check_password("Brand-new-pw-93!")


def test_reset_with_forged_token_is_rejected(client: Client, user: User) -> None:
    password_before = user.password

    response = client.post(
        _reset_url(user, token="abc-123"),
        data={"new_password1": "Brand-new-pw-93!", "new_password2": "Brand-new-pw-93!"},
    )

    assert response["Location"] == reverse("account:forgot-password")
    user.refresh_from_db()
    assert user.password == password_before


def test_reset_with_garbage_uid_is_rejected(client: Client) -> None:
    response = client.get(reverse("account:reset-password", kwargs={"uidb64": "!!", "token": "x-y"}))

    assert response["Location"] == reverse("account:forgot-password")
