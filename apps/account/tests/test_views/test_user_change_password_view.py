import http

import pytest
from django.contrib.auth import authenticate
from django.test import RequestFactory
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.test_utils import contains_attribute
from apps.account.views import UserChangePasswordView, UserDetailView

pytestmark = pytest.mark.django_db

NEW_PASSWORD = "my_new_password"


def test_get_regular(authenticated_client, user):
    response = authenticated_client.get(reverse("account:change-password", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserChangePasswordView.template_name
    assert "Change your password" in response.content.decode()


def test_post_regular(authenticated_client, user):
    response = authenticated_client.post(
        reverse("account:change-password", args=(user.id,)),
        data={
            "old_password": DEFAULT_PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password_confirmation": NEW_PASSWORD,
        },
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name
    assert "Your account overview" in response.content.decode()

    request = RequestFactory().get("/")
    assert authenticate(request=request, email=user.email, password=NEW_PASSWORD) == user


@pytest.mark.parametrize(
    ("data", "expected_field"),
    [
        ({}, "new_password"),
        ({"old_password": DEFAULT_PASSWORD}, "new_password"),
        ({"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD}, "new_password_confirmation"),
    ],
)
def test_post_without_every_password_re_renders_the_form(authenticated_client, user, data, expected_field):
    """The inputs are `required`, so only a client that skips them gets here — with a 500 before."""
    response = authenticated_client.post(reverse("account:change-password", args=(user.id,)), data=data)

    assert response.status_code == http.HTTPStatus.OK
    assert expected_field in response.context["form"].errors


def test_post_with_a_wrong_current_password_shows_the_error_on_the_field(authenticated_client, user):
    response = authenticated_client.post(
        reverse("account:change-password", args=(user.id,)),
        data={
            "old_password": "not-the-current-password",
            "new_password": NEW_PASSWORD,
            "new_password_confirmation": NEW_PASSWORD,
        },
    )

    assert response.status_code == http.HTTPStatus.OK
    assert "old_password" in response.context["form"].errors
    assert contains_attribute(response.content.decode(), "id", "old_passwordError")


def test_post_with_a_mismatched_confirmation_shows_the_error_on_the_confirmation(authenticated_client, user):
    response = authenticated_client.post(
        reverse("account:change-password", args=(user.id,)),
        data={
            "old_password": DEFAULT_PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password_confirmation": "something-else",
        },
    )

    assert response.status_code == http.HTTPStatus.OK
    assert "new_password_confirmation" in response.context["form"].errors
    assert contains_attribute(response.content.decode(), "id", "new_password_confirmationError")
