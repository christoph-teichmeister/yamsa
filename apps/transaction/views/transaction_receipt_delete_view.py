from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import generic
from apps.transaction.forms.transaction_receipt_upload_form import TransactionReceiptUploadForm
from apps.transaction.models import Receipt
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionReceiptDeleteView(TransactionBaseContext, generic.TemplateView):
    template_name = "transaction/partials/_receipts_section.html"

    def post(self, request, room_slug, receipt_pk):
        receipt = get_object_or_404(
            Receipt.objects.select_related("uploaded_by", "parent_transaction__room"),
            pk=receipt_pk,
            parent_transaction__room=request.room,
        )

        if receipt.uploaded_by_id != request.user.id:
            return HttpResponseForbidden("You can only delete receipts you uploaded.")

        parent_transaction = receipt.parent_transaction
        receipt.file.delete(save=False)
        receipt.delete()

        receipts = parent_transaction.receipts.select_related("uploaded_by").all()
        form = TransactionReceiptUploadForm(request=request)
        request.toast_queue.success("Receipt deleted.")

        context = self.get_context_data(
            parent_transaction=parent_transaction,
            receipts=receipts,
            receipt_upload_form=form,
        )

        response = self.render_to_response(context)
        return response
