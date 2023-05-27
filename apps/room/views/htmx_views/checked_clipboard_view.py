from django.views import generic


class CheckedClipboardHTMXView(generic.TemplateView):
    template_name = "shared_partials/clipboard_icon_checked.html"
