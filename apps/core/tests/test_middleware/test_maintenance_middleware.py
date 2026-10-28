from http import HTTPStatus

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from apps.core.middleware.maintenance_middleware import MaintenanceMiddleware


@pytest.mark.django_db
class TestMaintenanceMiddleware:
    @pytest.fixture(autouse=True)
    def _setup(self, settings: pytest.FixtureRequest) -> None:
        settings.MAINTENANCE = True
        self.middleware = MaintenanceMiddleware(lambda _request: HttpResponse(status=HTTPStatus.OK))
        self.factory = RequestFactory()

    def test_regular_path_redirects_to_maintenance_page(self) -> None:
        response = self.middleware(self.factory.get("/"))

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("core:maintenance")

    def test_path_merely_containing_maintenance_is_still_redirected(self) -> None:
        response = self.middleware(self.factory.get("/room/maintenance-crew/"))

        assert response.status_code == HTTPStatus.FOUND

    def test_maintenance_page_is_served(self) -> None:
        response = self.middleware(self.factory.get(reverse("core:maintenance")))

        assert response.status_code == HTTPStatus.OK

    def test_healthcheck_is_exempt(self) -> None:
        response = self.middleware(self.factory.get(reverse("core:healthcheck")))

        assert response.status_code == HTTPStatus.OK
