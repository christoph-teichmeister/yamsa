import json

from django.conf import settings
from django.views import generic


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/javascript"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cache_settings = settings.PWA_SERVICE_WORKER
        precache_urls = self._build_precache_urls(cache_settings)

        context.update(
            cache_name=cache_settings.get("cache_name", "yamsa-static-cache"),
            cache_prefix=cache_settings.get("cache_prefix", "yamsa-static-cache"),
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

        for url in cache_settings.get("precache_urls", []):
            if url:
                urls.add(str(url))

        for icon in manifest.get("icons", []):
            src = icon.get("src")
            if src:
                urls.add(src)

        for splash in manifest.get("splash_screens", []):
            src = splash.get("src")
            if src:
                urls.add(src)

        return sorted(urls)
