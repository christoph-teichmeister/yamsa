import json

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.views import generic
from webpack_loader.utils import get_files

from apps.core.pwa_constants import CACHED_AT_HEADER_NAME, PREFETCH_HEADER_NAME, SCOPE_HEADER_NAME
from apps.core.services.pwa_cache_version_service import resolve_cache_version


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/javascript"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cache_settings = settings.PWA_SERVICE_WORKER
        precache_urls = self._build_precache_urls(cache_settings)
        cache_prefix = cache_settings.get("cache_prefix", "yamsa")
        cache_version = resolve_cache_version()

        context.update(
            cache_name=f"{cache_prefix}-static-{cache_version}",
            # Trailing separator included: the worker cannot know the current visitor while it is
            # offline, so it recognises its page cache by this prefix rather than by a full name.
            pages_cache_prefix=f"{cache_prefix}-pages-{cache_version}-",
            cache_prefix=cache_prefix,
            offline_url=str(cache_settings.get("offline_url", "/offline/")),
            precache_urls=json.dumps(precache_urls),
            static_url_prefix=cache_settings.get("static_url_prefix", settings.STATIC_URL),
            max_cached_pages=cache_settings.get("max_cached_pages", 40),
            scope_header=SCOPE_HEADER_NAME,
            cached_at_header=CACHED_AT_HEADER_NAME,
            prefetch_header=PREFETCH_HEADER_NAME,
            session_url=reverse("core:pwa-session"),
            login_path=reverse("account:login"),
        )
        return context

    def _build_precache_urls(self, cache_settings):
        manifest = settings.MANIFEST
        urls = set()

        offline_url = cache_settings.get("offline_url")
        if offline_url:
            urls.add(str(offline_url))

        # Both lookups go through what the templates use, because only those answer with the URL
        # the browser will actually ask for: the storage hashes a static file's name, the webpack
        # loader reads the bundle's URL out of the stats file.
        for name in cache_settings.get("precache_static", []):
            if name:
                urls.add(staticfiles_storage.url(name))

        for bundle_name, extension in cache_settings.get("precache_bundles", {}).items():
            if not bundle_name:
                continue
            urls.update(chunk["url"] for chunk in get_files(bundle_name, extension))

        for icon in manifest.get("icons", []):
            src = icon.get("src")
            if src:
                urls.add(src)

        for splash in manifest.get("splash_screens", []):
            src = splash.get("src")
            if src:
                urls.add(src)

        return sorted(urls)
