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

    def get_queryset(self):
        return super().get_queryset().select_related("paid_by", "currency", "category")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            # Only allow editing the form values, when a form is posted
            form_kwargs["data"]._mutable = True

            # Clean up the mapping of multi-value fields
            multi_value_fields = ("value", "child_transaction_id", "paid_for")
            for field in multi_value_fields:
                form_kwargs["data"][field] = form_kwargs["data"].getlist(field)

        return form_kwargs

    def get_success_url(self):
        return reverse(
            viewname="transaction:detail",
            kwargs={"room_slug": self.request.room.slug, "pk": self.object.id},
        )

    @context
    @cached_property
    def child_transaction_qs(self):
        return self.get_object().child_transactions.all()
