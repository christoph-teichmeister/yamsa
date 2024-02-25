import http

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.account.views import LogInUserView
from apps.core.tests.setup import BaseTestSetUp


class LogOutUserViewTestCase(BaseTestSetUp):
    def test_get_regular_as_user_and_guest_user(self):
        for authenticated_user in [self.user, self.guest_user]:
            self.client.force_login(authenticated_user)
            response = self.client.get(reverse("account:logout"), follow=True)

            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertTrue(response.template_name[0], LogInUserView.template_name)

            self.assertIsInstance(response.wsgi_request.user, AnonymousUser)

            stringed_content = str(response.content)
            self.assertIn("Login", stringed_content)
            self.assertIn("Forgot password?", stringed_content)

            self.assertIn("have an account yet?", stringed_content)
            self.assertIn("Register here!", stringed_content)
