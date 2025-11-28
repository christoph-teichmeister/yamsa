from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
from apps.core.tests.setup import BaseTestSetUp


class SessionKeepAliveMiddlewareTestCase(BaseTestSetUp):
    def test_refreshes_session_ttl_on_authenticated_requests(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        session.set_expiry(30)
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        self.client.get(reverse("core:welcome"))

        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session.get_expiry_age())

    def test_maintains_remember_me_ttl(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SESSION_TTL_SESSION_KEY] = settings.DJANGO_REMEMBER_ME_SESSION_AGE
        session.set_expiry(30)
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        self.client.get(reverse("core:welcome"))

        self.assertEqual(settings.DJANGO_REMEMBER_ME_SESSION_AGE, self.client.session.get_expiry_age())

    def test_skips_safe_htmx_fragments(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        session.set_expiry(30)
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        self.client.get(
            reverse("core:welcome"),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TRIGGER="reminder-heartbeat",
        )

        self.assertEqual(30, self.client.session.get_expiry_age())
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session[SESSION_TTL_SESSION_KEY])

    @override_settings(SESSION_COOKIE_AGE=1)
    def test_session_expiry_follows_idle_threshold(self):
        session = self.client.session
        session[SESSION_TTL_SESSION_KEY] = settings.SESSION_COOKIE_AGE
        session.set_expiry(settings.SESSION_COOKIE_AGE)
        session.save()

        session.set_expiry(-1)
        session.save()

        response = self.client.get(reverse("core:welcome"), follow=True)

        self.assertRedirects(response, reverse("account:login"))
