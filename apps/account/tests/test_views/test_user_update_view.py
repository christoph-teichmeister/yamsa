import http
import json

import pytest
from django.test.client import Client
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import UserFactory
from apps.account.tests.test_utils import contains_attribute
from apps.account.views import UserDetailView

pytestmark = pytest.mark.django_db


@pytest.fixture
def plain_client(user) -> Client:
    """A client without the HX-Request header, standing in for a direct browser navigation."""

    client = Client()
    client.force_login(user)
    return client


class TestUserUpdateView:
    def test_get_foreign_account_forbidden(self, authenticated_client, user):
        other_user = UserFactory()

        response = authenticated_client.get(reverse("account:update", kwargs={"pk": other_user.id}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_post_foreign_account_forbidden(self, authenticated_client, user):
        other_user = UserFactory()
        original_name = other_user.name

        response = authenticated_client.post(
            reverse("account:update", kwargs={"pk": other_user.id}),
            data={"name": "hijacked", "email": other_user.email},
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        other_user.refresh_from_db()
        assert other_user.name == original_name

    def test_a_get_belongs_on_the_profile(self, authenticated_client, user):
        """There is no edit page left to land on — the profile itself is editable."""
        response = authenticated_client.get(reverse("account:update", kwargs={"pk": user.id}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response["Location"] == reverse("account:detail", kwargs={"pk": user.id})

    def test_post_answers_with_the_sheet_alone(self, authenticated_client, user):
        new_name = "new_name"

        response = authenticated_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={"name": new_name, "email": user.email},
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # Only the sheet, so the browser keeps the page it is on instead of reloading it.
        assert contains_attribute(content, "id", "profile-sheet")
        assert "<html" not in content

        user.refresh_from_db()
        assert user.name == new_name

    def test_post_triggers_the_webpush_subscription_update(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={
                "name": user.name,
                "email": user.email,
                "wants_to_receive_webpush_notifications": "on",
            },
        )

        assert json.loads(response.headers["HX-Trigger"]) == {"notificationsEnabled": True}

    def test_post_of_invalid_data_answers_with_the_sheet_and_the_error(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={"name": "", "email": "not-an-email"},
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # A rejected save keeps the typed values, or the corrections start from scratch.
        assert contains_attribute(content, "id", "profile-sheet")
        assert contains_attribute(content, "value", "not-an-email")
        assert "Enter a valid email address." in content

        user.refresh_from_db()
        assert user.email != "not-an-email"

    def test_post_of_a_new_language_asks_the_browser_to_reload(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={"name": user.name, "email": user.email, "language": "de"},
        )

        # Everything outside the sheet is still rendered in the previous language.
        assert response.headers["HX-Refresh"] == "true"

        user.refresh_from_db()
        assert user.language == "de"

    def test_post_without_htmx_redirects_to_the_profile(self, plain_client, user):
        new_name = "new_name"

        response = plain_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={"name": new_name, "email": user.email},
            follow=True,
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == UserDetailView.template_name

        user.refresh_from_db()
        assert user.name == new_name

    def test_post_keeps_working_for_the_login_password(self, authenticated_client, user):
        authenticated_client.post(
            reverse("account:update", kwargs={"pk": user.id}),
            data={"name": "renamed", "email": user.email},
        )

        user.refresh_from_db()
        assert user.check_password(DEFAULT_PASSWORD)
