import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.webpush.utils import get_templatetag_context

pytestmark = pytest.mark.django_db


class TestWebPushTemplateTagContext:
    def test_returns_expected_context_data(self, user):
        request = RequestFactory().get("/")
        request.user = user
        context = {"request": request, "webpush": {"group": "alerts"}}

        data = get_templatetag_context(context)

        assert data["webpush_save_url"] == reverse("webpush:save")
        assert data["group"] == "alerts"
        assert data["user"] == user
