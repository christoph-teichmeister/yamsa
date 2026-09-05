from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.importer.constants import TOKEN_PARAM
from apps.importer.dataclasses import ParsedImport
from apps.importer.forms import ImportUploadForm
from apps.importer.parsers.base import MAX_IMPORT_FILE_SIZE
from apps.importer.session import store_parsed_import


class ImportUploadView(mixins.LoginRequiredMixin, generic.FormView):
    template_name = "importer/upload.html"
    form_class = ImportUploadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["max_file_size_mb"] = MAX_IMPORT_FILE_SIZE // (1024 * 1024)
        return context

    def form_valid(self, form):
        parsed: ParsedImport = form.cleaned_data["parsed"]
        token = store_parsed_import(self.request.session, parsed.as_payload())
        return HttpResponseRedirect(f"{reverse('importer:preview')}?{TOKEN_PARAM}={token}")
