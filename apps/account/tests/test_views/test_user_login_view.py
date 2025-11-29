import http

import pytest
from django.conf import settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.views import LogInUserView
from apps.core.views import WelcomePartialView

pytestmark = pytest.mark.django_db


def test_get_regular(client):
    response = client.get(reverse("account:login"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == LogInUserView.template_name

    content = response.content.decode()
    assert "Login" in content
    assert "Forgot password?" in content
    assert "Create an account" in content
    assert "Welcome back" in content


def test_post_regular(client, user):
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": DEFAULT_PASSWORD},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == WelcomePartialView.template_name
    assert client.session[SESSION_TTL_SESSION_KEY] == settings.SESSION_COOKIE_AGE
    assert client.session.get_expiry_age() == settings.SESSION_COOKIE_AGE


def test_post_email_and_password_are_required(client):
    response = client.post(reverse("account:login"))

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    assert "This field is required" in content
    assert content.count("This field is required") >= 2


def test_post_with_remember_me_extends_session(client, user):
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": DEFAULT_PASSWORD, "remember_me": "on"},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert client.session.get_expiry_age() == settings.DJANGO_REMEMBER_ME_SESSION_AGE
    assert client.session[SESSION_TTL_SESSION_KEY] == settings.DJANGO_REMEMBER_ME_SESSION_AGE


def test_post_email_and_password_do_not_match(client, user):
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": "wrong_password"},
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == LogInUserView.template_name
    assert str(LogInUserView.ExceptionMessage.AUTH_FAILED) in response.content.decode()

    response = client.post(
        reverse("account:login"),
        data={"email": f"{user.email}-wrong", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == LogInUserView.template_name
    assert str(LogInUserView.ExceptionMessage.AUTH_FAILED) in response.content.decode()
