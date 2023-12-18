from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionEditView(TransactionBaseContext, generic.UpdateView):
    model = ParentTransaction
    form_class = TransactionEditForm
    template_name = "transaction/edit.html"
    context_object_name = "parent_transaction"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            # Only edit the value, when a form is posted
            form_kwargs["data"]._mutable = True
            # "Spread" the form-inputs for value and child_transaction_id
            form_kwargs["data"]["value"] = {**form_kwargs["data"]}["value"]
            form_kwargs["data"]["child_transaction_id"] = {**form_kwargs["data"]}.get("child_transaction_id")
            form_kwargs["data"]["paid_for"] = {**form_kwargs["data"]}.get("paid_for")

            form_kwargs["data"]["request_user"] = self.request.user

        return form_kwargs

    def get_success_url(self):
        return reverse(
            viewname="transaction-detail",
            kwargs={"room_slug": self.request.room.slug, "pk": self.object.id},
        )

    @context
    @cached_property
    def child_transaction_qs(self):
        return self.get_object().child_transactions.all()
