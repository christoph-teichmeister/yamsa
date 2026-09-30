import http
from collections.abc import Callable

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserPasskeyFactory
from apps.account.views import UserSecurityView

pytestmark = pytest.mark.django_db


class TestUserSecurityViewGet:
    def test_get_own_profile_no_passkey(self, hx_client: Callable, user: User):
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == UserSecurityView.template_name
        content = response.content.decode()
        assert "Register passkey" in content
        assert "Security settings" in content

    def test_get_own_profile_with_passkey(self, hx_client: Callable, user: User):
        passkey = UserPasskeyFactory(user=user)
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert passkey.name in content
        assert "Delete" in content
        assert "Register passkey" not in content

    def test_get_other_users_profile_is_forbidden(self, hx_client: Callable, user: User, superuser: User):
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": superuser.id}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_superuser_can_access_own_profile(self, superuser_htmx_client: Client, superuser: User):
        response = superuser_htmx_client.get(reverse("account:security", kwargs={"pk": superuser.id}))

        assert response.status_code == http.HTTPStatus.OK

    def test_get_requires_login(self, client: Client, user: User):
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert "login" in response["Location"]
