import http

import pytest
from django.urls import reverse
from playwright.sync_api import Page


@pytest.mark.e2e
class TestMaintenanceMode:
    @pytest.fixture(autouse=True)
    def _maintenance_on(self, settings: object) -> None:
        # The live server runs in this process, so the override reaches its requests too.
        settings.MAINTENANCE = True

    def test_regular_pages_redirect_to_the_maintenance_page(self, page: Page, base_url: str) -> None:
        page.goto(f"{base_url}/")

        assert page.url.endswith(reverse("core:maintenance"))

    def test_the_healthcheck_still_answers_during_maintenance(self, page: Page, base_url: str) -> None:
        response = page.request.get(f"{base_url}{reverse('core:healthcheck')}", max_redirects=0)

        assert response.status == http.HTTPStatus.OK
