import http

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.views import RegisterUserView
from apps.core.views import WelcomePartialView

pytestmark = pytest.mark.django_db


def test_get_regular(client):
    response = client.get(reverse("account:register"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name
    content = response.content.decode()
    assert "Register" in content
    assert "Already have an account?" in content
    assert "Login here!" in content


def test_get_from_invitation_email(client, guest_user):
    email_from_invitation_email = "invitation@local.local"
    response = client.get(
        f"{reverse('account:register')}?with_email={email_from_invitation_email}&for_guest={guest_user.id}"
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name

    assert response.context_data["email_from_invitation_email"] == email_from_invitation_email
    assert response.context_data["form"].initial["email"] == email_from_invitation_email
    assert response.context_data["form"].initial["id"] == str(guest_user.id)
    content = response.content.decode()
    assert "Register" in content
    assert "Already have an account?" in content
    assert "Login here!" in content


def test_post_regular(client, monkeypatch):
    new_name = "new_name"
    new_email = "new_email@local.local"
    new_password = "a_password"

    recorded_messages = []

    def handle_message(message):
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


def test_post_from_invitation_email(client, guest_user, monkeypatch):
    guest_name = "guest_name"
    guest_email = "guest_email@local.local"
    guest_password = "guest_password"

    recorded_messages = []

    def handle_message(message):
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)
    response = client.post(
        reverse("account:register"),
        data={
            "id": guest_user.id,
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


def test_post_from_invitation_email_preserves_room_membership(client, room, guest_user, monkeypatch):
    guest_name = "guest_room"
    guest_email = "guest_room@local.local"
    guest_password = "guest_password"

    recorded_messages = []

    def handle_message(message):
        recorded_messages.append(message)
        return message

    monkeypatch.setattr("apps.account.views.user_register_view.handle_message", handle_message)
    response = client.post(
        reverse("account:register"),
        data={
            "id": guest_user.id,
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


def test_post_email_invalid(client):
    response = client.post(reverse("account:register"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == RegisterUserView.template_name

    content = response.content.decode()
    assert content.count("This field is required") >= 3
