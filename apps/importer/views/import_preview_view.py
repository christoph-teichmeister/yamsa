from django.contrib.auth import mixins
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.currency.models import Currency
from apps.importer.constants import IMPORT_SHARE_HINT_SESSION_KEY, SESSION_KEY
from apps.importer.dataclasses import ParsedImport
from apps.importer.forms import ImportPreviewForm
from apps.importer.registry import get_parser
from apps.importer.services.import_service import ImportService
from apps.transaction.messages.events.transaction import TransactionsImported


class ImportPreviewView(mixins.LoginRequiredMixin, generic.FormView):
    template_name = "importer/preview.html"
    form_class = ImportPreviewForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and SESSION_KEY not in request.session:
            return redirect("importer:upload")
        return super().dispatch(request, *args, **kwargs)

    @property
    def parsed(self) -> ParsedImport:
        return ParsedImport.from_payload(self.request.session[SESSION_KEY])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["parsed"] = self.parsed
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        parsed = self.parsed
        initial.setdefault("room_name", " & ".join(parsed.people)[:100])
        description = _("Import from %(source)s") % {"source": self._source_label()}
        initial.setdefault("room_description", description[:50])

        codes = parsed.currency_codes
        if codes:
            match = Currency.objects.filter(code__iexact=codes[0]).order_by("id").first()
            if match:
                initial.setdefault("preferred_currency", match.pk)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parsed = self.parsed
        context["parsed"] = parsed
        context["source_label"] = self._source_label()
        context["date_range"] = parsed.date_range
        context["totals_by_currency"] = parsed.totals_by_currency()
        return context

    def form_valid(self, form):
        parsed = self.parsed
        service = ImportService(parsed=parsed, user=self.request.user)

        with transaction.atomic():
            result = service.process(
                room_name=form.cleaned_data["room_name"],
                room_description=form.cleaned_data["room_description"],
                currency=form.cleaned_data["preferred_currency"],
                person_assignments=form.cleaned_data["person_assignments"],
                category_assignments=form.cleaned_data["category_assignments"],
            )

        # Side effects belong outside the atomic block so no HTTP call holds the DB connection.
        handle_message(
            TransactionsImported(
                context_data={
                    "room": result.room,
                    "imported_count": result.transaction_count,
                    "settled_count": result.settlement_count,
                    "source_label": self._source_label(),
                    "triggered_by": self.request.user,
                }
            )
        )

        del self.request.session[SESSION_KEY]
        self.request.session[IMPORT_SHARE_HINT_SESSION_KEY] = str(result.room.slug)
        self.request.toast_queue.success(self._build_success_message(result))

        return HttpResponseRedirect(reverse("transaction:list", kwargs={"room_slug": result.room.slug}))

    def form_invalid(self, form):
        for error in form.non_field_errors():
            self.request.toast_queue.error(str(error))
        return super().form_invalid(form)

    def _build_success_message(self, result) -> str:
        message = _("%(count)d transactions imported") % {"count": result.transaction_count}
        if result.settlement_count:
            message += _(", %(count)d settlements") % {"count": result.settlement_count}
        if result.skipped_count:
            message += _(", %(count)d rows skipped") % {"count": result.skipped_count}
        return message

    def _source_label(self) -> str:
        return get_parser(self.parsed.source_key).label
