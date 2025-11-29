import http

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.account.views import LogInUserView

pytestmark = pytest.mark.django_db


def test_get_regular_as_user_and_guest_user(client, guest_user, user):
    for authenticated_user in (user, guest_user):
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(authenticated_user)

        response = client.get(reverse("account:logout"), follow=True)

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == LogInUserView.template_name
        assert isinstance(response.wsgi_request.user, AnonymousUser)

        content = response.content.decode()
        assert "Login" in content
        assert "Forgot password?" in content
        assert "Create an account" in content

        client.logout()
