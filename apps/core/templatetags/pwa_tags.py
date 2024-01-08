from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("core/pwa/load_meta_data.html", takes_context=True)
def load_pwa_meta_data(context):
    # Pass MANIFEST settings into the template
    return {"manifest": settings.MANIFEST}


@register.inclusion_tag("core/pwa/load_serviceworker.html", takes_context=True)
def load_serviceworker(context):
    # For some reason, context does not always have request
    # (See https://chris-teichmeister.sentry.io/issues/4814658034/?project=4506417250107392)
    # ...take care of this here
    user = None
    if hasattr(context, "request"):
        user = context.request.user

    # Pass some objects into the template
    return {
        "user": user,
        "manifest": settings.MANIFEST,
        "PWA_SERVICE_WORKER_DEBUG": settings.PWA_SERVICE_WORKER_DEBUG,
        "WEBPUSH_SETTINGS": settings.WEBPUSH_SETTINGS,
    }
