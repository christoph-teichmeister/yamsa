from django.contrib.auth import mixins
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.importer.constants import IMPORT_SHARE_HINT_SESSION_KEY, TOKEN_PARAM
from apps.importer.dataclasses import ParsedImport
from apps.importer.forms import ImportPreviewForm
from apps.importer.registry import get_parser
from apps.importer.services.import_service import ImportService
from apps.importer.session import pop_parsed_import, read_parsed_import, resolve_currencies_by_code
from apps.room.models import Room
from apps.transaction.messages.events.transaction import TransactionsImported


class ImportPreviewView(mixins.LoginRequiredMixin, generic.FormView):
    template_name = "importer/preview.html"
    form_class = ImportPreviewForm

    def dispatch(self, request, *args, **kwargs):
        # This runs before LoginRequiredMixin.dispatch, so anonymous visitors must fall through
        # to the mixin instead of being redirected to the upload page.
        if request.user.is_authenticated and self._payload is None:
            return redirect("importer:upload")
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def _token(self) -> str:
        return self.request.GET.get(TOKEN_PARAM, "") or self.request.POST.get(TOKEN_PARAM, "")

    @cached_property
    def _payload(self) -> dict | None:
        return read_parsed_import(self.request.session, self._token)

    @cached_property
    def parsed(self) -> ParsedImport:
        # Rebuilding this costs a full deserialisation of up to MAX_IMPORT_ROWS rows, and a POST
        # reads it half a dozen times.
        return ParsedImport.from_payload(self._payload)

    @cached_property
    def source_label(self) -> str:
        return get_parser(self.parsed.source_key).label

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["parsed"] = self.parsed
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        name_limit = Room._meta.get_field("name").max_length
        description_limit = Room._meta.get_field("description").max_length
        initial.setdefault("room_name", " & ".join(self.parsed.people)[:name_limit])
        description = _("Import from %(source)s") % {"source": self.source_label}
        initial.setdefault("room_description", description[:description_limit])

        currencies = resolve_currencies_by_code(self.parsed.currency_codes)
        for code in self.parsed.currency_codes:
            if currencies.get(code):
                initial.setdefault("preferred_currency", currencies[code].pk)
                break
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        currencies = resolve_currencies_by_code(self.parsed.currency_codes)
        context["parsed"] = self.parsed
        context["source_label"] = self.source_label
        context["date_range"] = self.parsed.date_range
        context["totals_by_currency"] = self.parsed.totals_by_currency()
        context["import_token"] = self._token
        # Codes without a Currency row are booked in the room's currency, which silently merges
        # foreign amounts into one balance — the user has to see that before confirming.
        context["unknown_currency_codes"] = [code for code in self.parsed.currency_codes if not currencies.get(code)]
        return context

    def form_valid(self, form):
        service = ImportService(parsed=self.parsed, user=self.request.user)

        with transaction.atomic():
            result = service.process(
                room_name=form.cleaned_data["room_name"],
                room_description=form.cleaned_data["room_description"],
                currency=form.cleaned_data["preferred_currency"],
                person_assignments=form.cleaned_data["person_assignments"],
                category_assignments=form.cleaned_data["category_assignments"],
            )

        # Consumed before the side effects: a handler that raises would otherwise leave the payload
        # in place and let a retry import the same file a second time.
        pop_parsed_import(self.request.session, self._token)

        # Both of these emit webpush/email, so they belong outside the atomic block (#333).
        # The event runs first because it recalculates the room's debts: handle_event re-raises,
        # so a failing connection mail would otherwise leave a room full of transactions and no
        # debts at all. In this order the same failure costs one missing membership instead.
        handle_message(
            TransactionsImported(
                context_data={
                    "room": result.room,
                    "imported_count": result.transaction_count,
                    "settled_count": result.settlement_count,
                    "source_label": self.source_label,
                    "triggered_by": self.request.user,
                }
            )
        )
        for user in result.deferred_connections:
            service.connect(user=user, room=result.room)

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
