import http

import pytest
from django.contrib.auth import authenticate
from django.test import RequestFactory
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
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
