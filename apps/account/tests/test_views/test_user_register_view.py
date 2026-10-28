import http

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import Client
from django.urls import reverse

from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.models import User
from apps.account.utils.guest_registration_token import build_guest_registration_token
from apps.account.views import RegisterUserView
from apps.core.views import WelcomePartialView
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def test_get_regular(client: Client) -> None:
    response = client.get(reverse("account:register"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name
    content = response.content.decode()
    assert "Register" in content
    assert "Already have an account?" in content
    assert "Login here!" in content


def test_get_from_invitation_email(client: Client, guest_user: User) -> None:
    email_from_invitation_email = "invitation@local.local"
    response = client.get(
        f"{reverse('account:register')}?with_email={email_from_invitation_email}"
        f"&guest_token={build_guest_registration_token(guest_user.id)}"
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name

    assert response.context_data["email_from_invitation_email"] == email_from_invitation_email
    assert response.context_data["form"].initial["email"] == email_from_invitation_email
    assert "id" not in response.context_data["form"].initial
    assert response.context_data["form"].instance == guest_user
    content = response.content.decode()
    assert "Register" in content
    assert "Already have an account?" in content
    assert "Login here!" in content


def test_post_regular(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
    new_name = "new_name"
    new_email = "new_email@local.local"
    new_password = "a_password"

    recorded_messages = []

    def handle_message(message: SendPostRegisterEmail) -> SendPostRegisterEmail:
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)
    response = client.post(
        reverse("account:register"),
        data={"name": new_name, "email": new_email, "password": new_password},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert isinstance(recorded_messages[0], SendPostRegisterEmail)

    assert response.template_name[0] == WelcomePartialView.template_name
    assert not isinstance(response.wsgi_request.user, AnonymousUser)
    assert response.wsgi_request.user.name == new_name
    assert response.wsgi_request.user.email == new_email


def test_post_from_invitation_email(client: Client, guest_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    guest_name = "guest_name"
    guest_email = "guest_email@local.local"
    guest_password = "guest_password"

    recorded_messages = []

    def handle_message(message: SendPostRegisterEmail) -> SendPostRegisterEmail:
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)
    response = client.post(
        reverse("account:register"),
        data={
            "guest_token": build_guest_registration_token(guest_user.id),
            "name": guest_name,
            "email": guest_email,
            "password": guest_password,
        },
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert isinstance(recorded_messages[0], SendPostRegisterEmail)

    assert response.template_name[0] == WelcomePartialView.template_name
    assert not isinstance(response.wsgi_request.user, AnonymousUser)
    assert response.wsgi_request.user.name == guest_name
    assert response.wsgi_request.user.email == guest_email

    guest_user.refresh_from_db()
    assert not guest_user.is_guest


def test_post_from_invitation_email_preserves_room_membership(
    client: Client, room: Room, guest_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    guest_name = "guest_room"
    guest_email = "guest_room@local.local"
    guest_password = "guest_password"

    recorded_messages = []

    def handle_message(message: SendPostRegisterEmail) -> SendPostRegisterEmail:
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)
    response = client.post(
        reverse("account:register"),
        data={
            "guest_token": build_guest_registration_token(guest_user.id),
            "name": guest_name,
            "email": guest_email,
            "password": guest_password,
        },
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert response.template_name[0] == WelcomePartialView.template_name

    guest_user.refresh_from_db()
    assert not guest_user.is_guest
    assert room.users.filter(id=guest_user.id).exists()
    assert response.wsgi_request.user.rooms.filter(id=room.id).exists()


def test_post_from_share_link_adds_user_to_room(client: Client, room: Room, monkeypatch: pytest.MonkeyPatch) -> None:
    share_url = reverse("room:share", kwargs={"share_hash": room.share_hash})
    client.get(share_url)

    new_name = "share_user"
    new_email = "share_user@local.local"
    new_password = "new_password"

    recorded_messages = []

    def handle_message(message: SendPostRegisterEmail) -> SendPostRegisterEmail:
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)

    response = client.post(
        reverse("account:register"),
        data={"name": new_name, "email": new_email, "password": new_password},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert len(recorded_messages) == 1
    assert isinstance(recorded_messages[0], SendPostRegisterEmail)

    assert response.template_name[0] == WelcomePartialView.template_name
    assert response.wsgi_request.user.rooms.filter(id=room.id).exists()


def test_post_email_invalid(client: Client) -> None:
    response = client.post(reverse("account:register"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name

    content = response.content.decode()
    assert content.count("This field is required") >= 3


def test_post_with_foreign_id_does_not_touch_that_account(client: Client, user: User) -> None:
    original_email = user.email
    original_password = user.password

    response = client.post(
        reverse("account:register"),
        data={"id": user.id, "name": "attacker", "email": "attacker@local.local", "password": "attacker_pw"},
    )

    assert response.status_code == http.HTTPStatus.FOUND
    user.refresh_from_db()
    assert (user.email, user.password) == (original_email, original_password)
    assert response.wsgi_request.user.id != user.id


def test_post_with_forged_guest_token_registers_a_new_account(client: Client, guest_user: User) -> None:
    client.post(
        reverse("account:register"),
        data={"guest_token": f"{guest_user.id}:forged", "name": "x", "email": "x@local.local", "password": "pw"},
    )

    guest_user.refresh_from_db()
    assert guest_user.is_guest
    assert User.objects.filter(email="x@local.local").exists()


def test_post_with_token_of_a_registered_user_does_not_touch_that_account(client: Client, user: User) -> None:
    original_email = user.email

    client.post(
        reverse("account:register"),
        data={
            "guest_token": build_guest_registration_token(user.id),
            "name": "x",
            "email": "x@local.local",
            "password": "pw",
        },
    )

    user.refresh_from_db()
    assert user.email == original_email


def test_post_as_logged_in_guest_converts_that_guest(client: Client, guest_user: User) -> None:
    client.force_login(guest_user)

    client.post(
        reverse("account:register"),
        data={"name": "now_real", "email": "now_real@local.local", "password": "pw"},
    )

    guest_user.refresh_from_db()
    assert not guest_user.is_guest
    assert guest_user.email == "now_real@local.local"
