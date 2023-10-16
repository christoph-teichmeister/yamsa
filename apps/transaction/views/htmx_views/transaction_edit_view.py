from django.forms import formset_factory
from django.shortcuts import render
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.core import htmx
from apps.transaction.forms.child_transaction_edit_form import ChildTransactionEditForm
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ParentTransaction


class TransactionEditHTMXView(htmx.FormHtmxResponseMixin, generic.UpdateView):
    model = ParentTransaction
    form_class = TransactionEditForm
    template_name = "transaction/_edit.html"
    context_object_name = "parent_transaction"

    toast_success_message = "Transaction successfully updated!"
    toast_error_message = "There was an error updating the transaction"

    @context
    @cached_property
    def child_transaction_formset(self):
        # TODO CT: This can be deleted and the original child_transactions can be used instead
        # Add child_transaction formset to get-request
        child_transaction_formset = formset_factory(ChildTransactionEditForm, extra=0)
        formset = child_transaction_formset(
            initial=[
                {
                    "id": child_transaction.id,
                    "paid_for": child_transaction.paid_for,
                    "value": child_transaction.value,
                    "room": child_transaction.parent_transaction.room,
                }
                for child_transaction in self.get_object().child_transactions.all()
            ]
        )

        return formset

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            # Only edit the value, when a form is posted
            form_kwargs["data"]._mutable = True
            form_kwargs["data"]["value"] = {**form_kwargs["data"]}["value"]
            form_kwargs["data"]["child_transaction_id"] = {**form_kwargs["data"]}["child_transaction_id"]

            form_kwargs["data"]["request_user"] = self.request.user

        return form_kwargs

    def get_response(self):
        parent_transaction = self.get_object()
        return render(
            request=self.request,
            template_name="transaction/_detail.html",
            status=201,
            context={
                "room": parent_transaction.room,
                "parent_transaction": parent_transaction,
                "child_transactions": parent_transaction.child_transactions.all(),
            },
        )
