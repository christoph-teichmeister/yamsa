from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.importer.constants import SESSION_KEY
from apps.importer.dataclasses import ParsedImport
from apps.importer.forms import ImportUploadForm


class ImportUploadView(mixins.LoginRequiredMixin, generic.FormView):
    template_name = "importer/upload.html"
    form_class = ImportUploadForm

    def form_valid(self, form):
        parsed: ParsedImport = form.cleaned_data["parsed"]
        # The upload itself is never persisted — only its parsed result travels to the next step.
        self.request.session[SESSION_KEY] = parsed.as_payload()
        return HttpResponseRedirect(reverse("importer:preview"))
