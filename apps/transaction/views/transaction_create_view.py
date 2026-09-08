import json
import uuid

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomNotClosedRequiredMixin
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ParentTransaction
from apps.transaction.services.category_suggestion_service import CategorySuggestionService
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext

CLIENT_REQUEST_ID_FIELD = "client_request_id"


class TransactionCreateView(RoomNotClosedRequiredMixin, TransactionBaseContext, generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "transaction/create.html"

    _active_tab = "transaction"

    def get_success_url(self):
        return reverse("transaction:list", kwargs={"room_slug": self.request.room.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("request", self.request)
        kwargs.setdefault("room", self.request.room)
        return kwargs

    def form_invalid(self, form):
        toast_message = self._get_toast_error_message(form)
        if toast_message:
            self.request.toast_queue.error(toast_message)
        return super().form_invalid(form)

    def form_valid(self, form):
        client_request_id = self._client_request_id()
        if client_request_id:
            if ParentTransaction.objects.filter(client_request_id=client_request_id).exists():
                return self._already_booked()
            form.instance.client_request_id = client_request_id

        try:
            with transaction.atomic():
                self.object = form.save()
        except forms.ValidationError as exc:
            # The model's full_clean() reports the unique index as a validation error, which is what
            # a replay looks like when the first attempt landed between the check above and here.
            if client_request_id and self._names_the_client_request_id(exc):
                return self._already_booked()
            if self._attach_validation_error(form, exc):
                return self.form_invalid(form)
            raise
        except IntegrityError:
            # Two replays racing each other: the loser never saw a row to check against.
            if client_request_id:
                return self._already_booked()
            raise

        handle_message(
            ParentTransactionCreated(context_data={"parent_transaction": self.object, "room": self.object.room})
        )
        return HttpResponseRedirect(self.get_success_url())

    def _client_request_id(self) -> str | None:
        """The name the client gave this submission, if it gave a usable one.

        Read here rather than through the form: it is not the visitor's input, it decides whether
        the submission is handled at all, and a form field would answer a replay with a "already
        exists" error instead of the transaction the visitor is looking for.
        """
        raw = self.request.POST.get(CLIENT_REQUEST_ID_FIELD)
        if not raw:
            return None

        try:
            return str(uuid.UUID(raw))
        except ValueError:
            # Nothing to protect if the client cannot name its own request; booking it once is
            # still better than refusing it.
            return None

    def _already_booked(self):
        """Answer a replay with the outcome of the submission that got here first.

        No event: the transaction exists, so its debts were recalculated and everyone was notified
        when it was created.
        """
        return HttpResponseRedirect(self.get_success_url())

    @staticmethod
    def _names_the_client_request_id(exc) -> bool:
        return CLIENT_REQUEST_ID_FIELD in (getattr(exc, "error_dict", None) or {})

    def _attach_validation_error(self, form, exc):
        error_dict = getattr(exc, "error_dict", None)
        if error_dict:
            for field_name, errors in error_dict.items():
                target_field = None if field_name == NON_FIELD_ERRORS else field_name
                for error in errors:
                    form.add_error(target_field, error)
            return True

        error_list = getattr(exc, "error_list", None)
        if error_list:
            receipt_errors = []
            for error in error_list:
                message = str(error).lower()
                if "receipt" in message:
                    receipt_errors.append(error)
            if receipt_errors:
                for error in receipt_errors:
                    form.add_error("receipts", error)
                return True

            for error in error_list:
                form.add_error(None, error)
            return True

        return False

    def _get_toast_error_message(self, form):
        non_field_errors = form.non_field_errors()
        if non_field_errors:
            return str(non_field_errors[0])
        for errors in form.errors.values():
            if errors:
                return str(errors[0])
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_datetime"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        # Minted per rendered form rather than in the browser, so a submission that never reaches
        # JavaScript still carries one.
        context["client_request_id"] = uuid.uuid4()
        context["selected_paid_for"] = self._build_selected_paid_for()

        form = context.get("form")

        context["selected_paid_by"] = self._build_selected_paid_by(form)
        context["selected_currency"] = self._build_selected_currency(form)
        suggestion_index = CategorySuggestionService(room=self.request.room).build_index()
        # An empty index would still render as "{}" and switch the suggestion markup on.
        context["category_suggestion_index"] = json.dumps(suggestion_index) if suggestion_index else ""

        return context

    def _build_selected_paid_for(self):
        if self.request.method == "POST":
            return [str(user_id) for user_id in self.request.POST.getlist("paid_for")]
        return [str(user_id) for user_id in self.request.room.users.values_list("id", flat=True)]

    def _build_selected_paid_by(self, form):
        posted = self.request.POST.get("paid_by")
        if posted:
            return posted
        if form:
            value = form["paid_by"].value()
            if value:
                return str(value)
        return str(self.request.user.id)

    def _build_selected_currency(self, form):
        if self.request.method == "POST":
            posted = self.request.POST.get("currency")
            if posted:
                return posted
        if form:
            value = form["currency"].value()
            if value:
                return str(value)
        return str(self.request.room.preferred_currency.id)
