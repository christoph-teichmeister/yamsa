import http

import pytest
from django.urls import reverse
from passkeys.models import UserPasskey

from apps.account.tests.factories import UserPasskeyFactory

pytestmark = pytest.mark.django_db


class TestPasskeyDeleteView:
    def test_post_deletes_own_passkey(self, hx_client, user):
        passkey = UserPasskeyFactory(user=user)
        client = hx_client(user)
        response = client.post(
            reverse("account:passkey-delete"),
            data={"id": passkey.id},
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert not UserPasskey.objects.filter(id=passkey.id).exists()

    def test_post_cannot_delete_other_users_passkey(self, hx_client, user, superuser):
        passkey = UserPasskeyFactory(user=superuser)
        client = hx_client(user)
        response = client.post(
            reverse("account:passkey-delete"),
            data={"id": passkey.id},
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert UserPasskey.objects.filter(id=passkey.id).exists()

    def test_post_requires_login(self, client, user):
        passkey = UserPasskeyFactory(user=user)
        response = client.post(
            reverse("account:passkey-delete"),
            data={"id": passkey.id},
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert "login" in response["Location"]
        assert UserPasskey.objects.filter(id=passkey.id).exists()
