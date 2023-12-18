from django.views import generic


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/x-javascript"
