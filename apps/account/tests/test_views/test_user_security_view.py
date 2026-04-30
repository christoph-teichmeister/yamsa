import http

import pytest
from django.urls import reverse

from apps.account.tests.factories import UserPasskeyFactory
from apps.account.views import UserSecurityView

pytestmark = pytest.mark.django_db


class TestUserSecurityViewGet:
    def test_get_own_profile_no_passkey(self, hx_client, user):
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == UserSecurityView.template_name
        content = response.content.decode()
        assert "Register passkey" in content
        assert "Security settings" in content

    def test_get_own_profile_with_passkey(self, hx_client, user):
        passkey = UserPasskeyFactory(user=user)
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        assert passkey.name in content
        assert "Delete" in content
        assert "Register passkey" not in content

    def test_get_other_users_profile_is_forbidden(self, hx_client, user, superuser):
        client = hx_client(user)
        response = client.get(reverse("account:security", kwargs={"pk": superuser.id}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_superuser_can_access_own_profile(self, superuser_htmx_client, superuser):
        response = superuser_htmx_client.get(reverse("account:security", kwargs={"pk": superuser.id}))

        assert response.status_code == http.HTTPStatus.OK

    def test_get_requires_login(self, client, user):
        response = client.get(reverse("account:security", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert "login" in response["Location"]
