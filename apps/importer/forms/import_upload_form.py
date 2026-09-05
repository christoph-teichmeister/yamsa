import os

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.importer.parsers.base import MAX_IMPORT_FILE_SIZE
from apps.importer.parsers.exceptions import ImportParseError
from apps.importer.registry import get_parser, get_source_choices


class ImportUploadForm(forms.Form):
    source = forms.ChoiceField(choices=get_source_choices, label=_("Source"))
    file = forms.FileField(label=_("Export file"))

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get("source")
        uploaded_file = cleaned_data.get("file")
        if not source or not uploaded_file:
            return cleaned_data

        parser = get_parser(source)

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in parser.accepted_extensions:
            expected = ", ".join(parser.accepted_extensions)
            raise forms.ValidationError({"file": _("Please upload a %(extensions)s file.") % {"extensions": expected}})

        if uploaded_file.size == 0:
            raise forms.ValidationError({"file": _("The file is empty.")})

        if uploaded_file.size > MAX_IMPORT_FILE_SIZE:
            raise forms.ValidationError({"file": _("The file must be 2 MB or smaller.")})

        uploaded_file.seek(0)
        try:
            cleaned_data["parsed"] = parser.parse(uploaded_file)
        except ImportParseError as error:
            raise forms.ValidationError({"file": str(error)}) from error

        parsed = cleaned_data["parsed"]
        if not parsed.transactions and not parsed.settlements:
            raise forms.ValidationError({"file": _("No importable rows found in this file.")})

        return cleaned_data
