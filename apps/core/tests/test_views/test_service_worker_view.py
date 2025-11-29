import json

from django.test import override_settings

from apps.core.views.service_worker_view import ServiceWorkerView


@override_settings(
    MANIFEST={
        "icons": [{"src": "/static/images/icons/icon.png"}],
        "splash_screens": [{"src": "/static/images/splash/splash.png"}],
    },
    PWA_SERVICE_WORKER={
        "cache_name": "test-cache",
        "cache_prefix": "test-prefix",
        "offline_url": "/offline-custom/",
        "precache_urls": ["/app.js", "", None],
        "static_url_prefix": "/custom-static/",
    },
    STATIC_URL="/static/",
)
def test_service_worker_builds_precache_urls_from_manifest():
    view = ServiceWorkerView()
    context = view.get_context_data()

    assert context["cache_name"] == "test-cache"
    assert context["cache_prefix"] == "test-prefix"
    assert context["offline_url"] == "/offline-custom/"
    assert context["static_url_prefix"] == "/custom-static/"

    precache_urls = json.loads(context["precache_urls"])
    assert precache_urls == [
        "/app.js",
        "/offline-custom/",
        "/static/images/icons/icon.png",
        "/static/images/splash/splash.png",
    ]
