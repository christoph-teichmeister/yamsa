import json
from http import HTTPStatus
from typing import Any

from django.http import HttpResponse
from django.urls import reverse


class FormHtmxResponseMixin:
    """
    FormView mixin for HTMX integration with Django forms.

    Features:
    - Add toast messages for success/error states
    - Set custom HX-Trigger events for HTMX
    """

    # TODO CT: This is not used anywhere?

    # Class constants for styling
    SUCCESS_TOAST_CLASS = "text-bg-success bg-gradient"
    ERROR_TOAST_CLASS = "text-bg-danger bg-gradient"

    # Configuration attributes
    hx_trigger: str | dict[str, Any] = {}
    default_success_url: str = "core:welcome"
    toast_success_message: str | None = None
    toast_error_message: str | None = None

    def get_success_url(self):
        return reverse(viewname=self.default_success_url)

    def form_valid(self, form):
        super().form_valid(form)
        response = self.get_response()

        # Process HX-Trigger
        hx_trigger = self.get_hx_trigger()
        if isinstance(hx_trigger, str):
            hx_trigger = {f"{hx_trigger}": True}

        # Add success toast if configured
        success_toast = self._create_toast_trigger(
            message=self.get_toast_success_message(), toast_class=self.SUCCESS_TOAST_CLASS
        )
        if success_toast:
            hx_trigger.update(success_toast)

        # Set HX-Trigger header if we have triggers
        if hx_trigger:
            response["HX-Trigger-After-Settle"] = json.dumps(hx_trigger)

        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)

        # Add error toast if configured
        error_toast = self._create_toast_trigger(
            message=self.get_toast_error_message(), toast_class=self.ERROR_TOAST_CLASS
        )
        if error_toast:
            response["HX-Trigger-After-Settle"] = json.dumps(error_toast)

        return response

    def _create_toast_trigger(self, *, message, toast_class):
        """Helper method to create toast trigger data"""
        if message:
            return {"triggerToast": {"message": message, "type": toast_class}}
        return {}

    # Getter methods for dynamic configuration

    def get_hx_trigger(self) -> str | dict[str, Any]:
        """Get trigger events for HTMX"""
        return self.hx_trigger

    def get_toast_success_message(self) -> str | None:
        """Get success message for toast notification"""
        return self.toast_success_message

    def get_toast_error_message(self) -> str | None:
        """Get error message for toast notification"""
        return self.toast_error_message

    def get_response(self) -> HttpResponse:
        """Create response object, can be overridden by subclasses"""
        return HttpResponse(HTTPStatus.OK)
