import time

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
from apps.core.tests.setup import BaseTestSetUp


class SessionKeepAliveMiddlewareTestCase(BaseTestSetUp):
    def test_refreshes_session_ttl_on_authenticated_requests(self):
        self.client.session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        self.client.session.set_expiry(30)
        self.client.session.save()

        self.client.get(reverse("core:welcome"))

        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session.get_expiry_age())

    def test_maintains_remember_me_ttl(self):
        self.client.session[SESSION_TTL_SESSION_KEY] = settings.DJANGO_REMEMBER_ME_SESSION_AGE
        self.client.session.set_expiry(30)
        self.client.session.save()

        self.client.get(reverse("core:welcome"))

        self.assertEqual(settings.DJANGO_REMEMBER_ME_SESSION_AGE, self.client.session.get_expiry_age())

    def test_skips_safe_htmx_fragments(self):
        self.client.session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        self.client.session.set_expiry(30)
        self.client.session.save()

        self.client.get(
            reverse("core:welcome"),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TRIGGER="reminder-heartbeat",
        )

        self.assertLess(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session[SESSION_TTL_SESSION_KEY])

    @override_settings(SESSION_COOKIE_AGE=1)
    def test_session_expiry_follows_idle_threshold(self):
        self.client.session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        self.client.session.set_expiry(settings.SESSION_COOKIE_AGE)
        self.client.session.save()

        time.sleep(1.1)
        response = self.client.get(reverse("core:welcome"), follow=True)

        self.assertRedirects(response, reverse("account:login"))
