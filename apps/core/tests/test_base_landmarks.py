import http

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse


def _login_page(client: Client) -> BeautifulSoup:
    response = client.get(reverse("account:login"))
    assert response.status_code == http.HTTPStatus.OK
    return BeautifulSoup(response.content.decode(), "html.parser")


def test_base_template_offers_a_skip_link_to_the_main_landmark(db: None, client: Client) -> None:
    page = _login_page(client)

    assert page.select_one('a[href="#base-content"]') is not None
    assert page.select_one("main#base-content") is not None


def test_toast_live_regions_are_rendered_empty(db: None, client: Client) -> None:
    page = _login_page(client)

    for region_id in ("toast-live-polite", "toast-live-assertive"):
        region = page.select_one(f"#{region_id}")
        assert region is not None
        assert region.get_text(strip=True) == ""
