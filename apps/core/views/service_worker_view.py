import json

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views import generic
from webpack_loader.utils import get_files

from apps.core.services.pwa_cache_version_service import resolve_cache_version


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/javascript"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cache_settings = settings.PWA_SERVICE_WORKER
        precache_urls = self._build_precache_urls(cache_settings)
        cache_prefix = cache_settings.get("cache_prefix", "yamsa")

        context.update(
            cache_name=f"{cache_prefix}-static-{resolve_cache_version()}",
            cache_prefix=cache_prefix,
            offline_url=str(cache_settings.get("offline_url", "/offline/")),
            precache_urls=json.dumps(precache_urls),
            static_url_prefix=cache_settings.get("static_url_prefix", settings.STATIC_URL),
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
