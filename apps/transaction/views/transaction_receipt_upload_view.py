import json

from django import forms
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import generic

from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.room.models import Room
from apps.transaction.forms.transaction_receipt_upload_form import TransactionReceiptUploadForm
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionReceiptUploadView(TransactionBaseContext, generic.TemplateView):
    template_name = "transaction/partials/_receipts_section.html"

    def post(self, request, room_slug, pk):
        if request.room.status == Room.StatusChoices.CLOSED:
            return HttpResponseForbidden("Cannot upload receipts to a closed room.")

        parent_transaction = get_object_or_404(
            ParentTransaction.objects.select_related("paid_by", "currency", "category"),
            pk=pk,
            room=request.room,
        )

        form = TransactionReceiptUploadForm(data=request.POST, files=request.FILES, request=request)
        upload_success = False
        hx_trigger_payload: dict[str, dict[str, str]] = {}

        if form.is_valid():
            try:
                form.save(parent_transaction)
            except forms.ValidationError as exc:
                form.add_error(None, exc)
            else:
                upload_success = True
                form = TransactionReceiptUploadForm(request=request)
                hx_trigger_payload["triggerToast"] = {
                    "message": "Receipt uploaded successfully.",
                    "type": SUCCESS_TOAST_CLASS,
                }

        receipts = parent_transaction.receipts.select_related("uploaded_by").all()

        context = self.get_context_data(
            parent_transaction=parent_transaction,
            receipts=receipts,
            receipt_upload_form=form,
            upload_success=upload_success,
        )

        response = self.render_to_response(context)
        if hx_trigger_payload:
            serialized_payload = json.dumps(hx_trigger_payload)
            response["HX-Trigger"] = serialized_payload
            response["HX-Trigger-After-Settle"] = serialized_payload
        return response
