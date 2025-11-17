from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.transaction.forms.transaction_receipt_upload_form import TransactionReceiptUploadForm
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionDetailView(TransactionBaseContext, generic.DetailView):
    model = ParentTransaction
    context_object_name = "parent_transaction"
    template_name = "transaction/detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("paid_by", "currency", "category")
            .prefetch_related("receipts__uploaded_by")
        )

    @context
    @cached_property
    def child_transactions(self):
        return self.object.child_transactions.all()

    @context
    @cached_property
    def receipts(self):
        return self.object.receipts.select_related("uploaded_by").all()

    @context
    def receipt_upload_form(self):
        return TransactionReceiptUploadForm(request=self.request)
