import json
import re

from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import Context, Template
from django.test import override_settings
from django.urls import reverse

from apps.core.views.service_worker_view import ServiceWorkerView


@override_settings(
    MANIFEST={
        "icons": [{"src": "/static/images/icons/icon.png"}],
        "splash_screens": [{"src": "/static/images/splash/splash.png"}],
    },
    PWA_SERVICE_WORKER={
        "cache_prefix": "test-prefix",
        "offline_url": "/offline-custom/",
        "precache_static": ["app.css", "", None],
        "precache_bundles": {"navigation": "js", "": "js"},
        "static_url_prefix": "/custom-static/",
    },
    STATIC_URL="/static/",
    SENTRY_RELEASE="release/1",
)
def test_service_worker_builds_precache_urls_from_manifest():
    view = ServiceWorkerView()
    context = view.get_context_data()

    assert context["cache_name"] == "test-prefix-static-release-1"
    assert context["cache_prefix"] == "test-prefix"
    assert context["offline_url"] == "/offline-custom/"
    assert context["static_url_prefix"] == "/custom-static/"

    precache_urls = json.loads(context["precache_urls"])
    assert precache_urls == [
        "/offline-custom/",
        "/static/app.css",
        "/static/images/icons/icon.png",
        "/static/images/splash/splash.png",
        "http://localhost/static/webpack_bundles/test.bundle.js",
    ]


@override_settings(
    MANIFEST={},
    PWA_SERVICE_WORKER={
        "offline_url": "/offline/",
        "precache_static": ["base.css"],
        "precache_bundles": {},
    },
)
def test_service_worker_precaches_the_url_the_storage_serves(monkeypatch):
    """A hashing storage renames every static file; precaching the raw name would cache nothing."""
    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}.deadbeef.css")

    precache_urls = json.loads(ServiceWorkerView().get_context_data()["precache_urls"])

    assert precache_urls == ["/offline/", "/static/base.css.deadbeef.css"]


def test_service_worker_precaches_every_asset_the_page_pulls_in():
    """An asset the page asks for but the worker skips is a page that loses it offline."""
    precached = set(json.loads(ServiceWorkerView().get_context_data()["precache_urls"]))

    head = Template("{% include 'core/partials/_head_links_and_scripts.html' %}").render(Context())
    stylesheets = set(re.findall(r"<link[^>]+href=\"([^\"]+)\"", head))
    assert stylesheets
    assert stylesheets <= precached

    icon = Template('{% icon "x-lg" %}').render(Context())
    sprite_url = re.search(r'href="([^"#]+)#', icon).group(1)
    assert sprite_url in precached


def test_service_worker_never_answers_app_assets_from_the_cache_first(client):
    """Guards the invariant that made bundle changes invisible until the caches were cleared."""
    script = client.get(reverse("core:serviceworker")).content.decode()

    assert "cacheFirst" not in script
    assert re.search(
        r"if \(isDocument \|\| isAppAsset\) \{\s*event\.respondWith\(networkFirst\(request\)\);",
        script,
    )
