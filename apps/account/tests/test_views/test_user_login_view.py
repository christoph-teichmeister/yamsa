import http

import pytest
from axes.models import AccessAttempt
from bs4 import BeautifulSoup
from django.conf import settings
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.views import LogInUserView
from apps.core.views import WelcomePartialView

pytestmark = pytest.mark.django_db


def test_post_with_empty_passkeys_field_still_authenticates_with_password(client: Client, user: User) -> None:
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": DEFAULT_PASSWORD, "passkeys": ""},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == WelcomePartialView.template_name


def test_get_regular(client: Client) -> None:
    response = client.get(reverse("account:login"))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == LogInUserView.template_name

    content = response.content.decode()
    assert "Login" in content
    assert "Forgot password?" in content
    assert "Create an account" in content
    assert "Welcome back" in content


def test_post_regular(client: Client, user: User) -> None:
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": DEFAULT_PASSWORD},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == WelcomePartialView.template_name
    assert client.session[SESSION_TTL_SESSION_KEY] == settings.SESSION_COOKIE_AGE
    assert client.session.get_expiry_age() == settings.SESSION_COOKIE_AGE


def test_post_email_and_password_are_required(client: Client) -> None:
    response = client.post(reverse("account:login"))

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    assert "This field is required" in content
    assert content.count("This field is required") >= 2


def test_post_with_remember_me_extends_session(client: Client, user: User) -> None:
    response = client.post(
        reverse("account:login"),
        data={"email": user.email, "password": DEFAULT_PASSWORD, "remember_me": "on"},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert client.session.get_expiry_age() == settings.DJANGO_REMEMBER_ME_SESSION_AGE
    assert client.session[SESSION_TTL_SESSION_KEY] == settings.DJANGO_REMEMBER_ME_SESSION_AGE


def test_post_email_and_password_do_not_match(client: Client, user: User) -> None:
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


def test_axes_tracks_email_as_username(client: Client, user: User) -> None:
    client.defaults["HTTP_HOST"] = "127.0.0.1"
    login_url = reverse("account:login")
    AccessAttempt.objects.all().delete()

    response = client.post(login_url, data={"email": user.email, "password": "wrong_password"})

    assert response.status_code == http.HTTPStatus.OK
    attempt = AccessAttempt.objects.filter(username=user.email).first()

    assert attempt is not None
    assert attempt.username == user.email


def test_axes_blocks_after_failure_limit(client: Client, user: User) -> None:
    client.defaults["HTTP_HOST"] = "127.0.0.1"
    login_url = reverse("account:login")
    AccessAttempt.objects.all().delete()

    attempts_before_lockout = max(settings.AXES_LOGIN_FAILURE_LIMIT - 1, 0)
    for _ in range(attempts_before_lockout):
        response = client.post(login_url, data={"email": user.email, "password": "wrong_password"})

        assert response.status_code == http.HTTPStatus.OK

    locked_response = client.post(login_url, data={"email": user.email, "password": "wrong_password"})

    assert locked_response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS


def test_axes_lockout_tracks_username_and_ip_scope(client: Client, user: User) -> None:
    client.defaults["HTTP_HOST"] = "127.0.0.1"
    login_url = reverse("account:login")
    AccessAttempt.objects.all().delete()

    # AXES_LOCKOUT_PARAMETERS pairs username and ip_address as the lockout tuple,
    # so supply the headers Axes will inspect.
    assert settings.AXES_LOCKOUT_PARAMETERS == [["username", "ip_address"]]

    def wrong_password_post(ip_address: str) -> HttpResponse:
        meta = {"REMOTE_ADDR": ip_address, "HTTP_X_FORWARDED_FOR": ip_address}
        return client.post(
            login_url,
            data={"email": user.email, "password": "wrong_password"},
            **meta,
        )

    first_ip = "10.0.0.1"
    second_ip = "10.0.0.2"
    # AXES_CLIENT_IP_CALLABLE may prefer REMOTE_ADDR or HTTP_X_FORWARDED_FOR, so send both.
    failure_limit = settings.AXES_LOGIN_FAILURE_LIMIT
    attempts_before_lockout = max(failure_limit - 1, 0)

    for _ in range(attempts_before_lockout):
        attempt_response = wrong_password_post(first_ip)
        assert attempt_response.status_code == http.HTTPStatus.OK

    locked_response = wrong_password_post(first_ip)
    assert locked_response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS

    # The same username is still allowed to authenticate from another IP.
    successful_response = client.post(
        login_url,
        data={"email": user.email, "password": DEFAULT_PASSWORD},
        REMOTE_ADDR=second_ip,
        HTTP_X_FORWARDED_FOR=second_ip,
        follow=True,
    )

    assert successful_response.status_code == http.HTTPStatus.OK
    assert successful_response.template_name[0] == WelcomePartialView.template_name


@pytest.mark.parametrize("source", ["post", "get"])
def test_login_returns_to_the_page_that_asked_for_it(client: Client, user: User, source: str) -> None:
    target = "/some/deep/page/"
    url = reverse("account:login")
    data = {"email": user.email, "password": DEFAULT_PASSWORD}
    if source == "post":
        response = client.post(url, data={**data, "next": target})
    else:
        response = client.post(f"{url}?next={target}", data=data)

    assert response.status_code == http.HTTPStatus.FOUND
    assert response.url == target


@pytest.mark.parametrize("target", ["https://evil.example/phish", "//evil.example/phish", "javascript:alert(1)"])
def test_login_ignores_a_next_that_leaves_the_host(client: Client, user: User, target: str) -> None:
    response = client.post(
        reverse("account:login"), data={"email": user.email, "password": DEFAULT_PASSWORD, "next": target}
    )

    assert response.status_code == http.HTTPStatus.FOUND
    assert response.url == reverse("core:welcome")


def test_login_form_carries_a_safe_next_through_a_failed_attempt(client: Client, user: User) -> None:
    response = client.post(
        reverse("account:login"), data={"email": user.email, "password": "wrong", "next": "/some/deep/page/"}
    )

    page = BeautifulSoup(response.content.decode(), "html.parser")
    assert page.select_one("input[name=next]")["value"] == "/some/deep/page/"


def test_login_page_offers_a_language_switch(client: Client) -> None:
    page = BeautifulSoup(client.get(reverse("account:login")).content.decode(), "html.parser")

    assert page.select_one(f"form[action='{reverse('set_language')}']") is not None
    assert {button["value"] for button in page.select("button[name=language]")} == {"en", "de"}
