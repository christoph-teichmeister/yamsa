from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("core/pwa/load_meta_data.html", takes_context=True)
def load_pwa_meta_data(context):
    # Pass MANIFEST settings into the template
    return {"manifest": settings.MANIFEST}


@register.inclusion_tag("core/pwa/load_serviceworker.html", takes_context=True)
def load_serviceworker(context):
    # Pass MANIFEST settings into the template
    return {
        "manifest": settings.MANIFEST,
        "PWA_SERVICE_WORKER_DEBUG": settings.PWA_SERVICE_WORKER_DEBUG,
        "WEBPUSH_SETTINGS": settings.WEBPUSH_SETTINGS,
    }
