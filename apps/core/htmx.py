import json
from typing import Dict, Union

from django.http import HttpResponse
from django.urls import reverse

from apps.core.http_status import HttpStatus


class FormHtmxResponseMixin:
    """
    FormView mixin to be able to simply set "HX-Redirect" and "HX-Trigger" for using HTMX in the frontend.
    "hx_redirect_url": Takes a reverse_lazy URL to a valid Django URL
    "hx_trigger": Takes either a string "updateComponentX" or a dictionary with a key-value-pair, where the key is
    the signal and the value is a parameter passed to the frontend. If you don't need the value, set it to None.
    """

    hx_trigger: Union[str, Dict[str, str]] = None

    toast_success_message: str = None
    toast_error_message: str = None

    def get_success_url(self):
        return reverse(viewname="core-welcome")

    def form_valid(self, form):
        super().form_valid(form)

        response = self.get_response()

        # Get attributes
        hx_trigger = self.get_hx_trigger()

        if isinstance(hx_trigger, str):
            hx_trigger = {f"{hx_trigger}": True}

        if hx_trigger is None:
            hx_trigger = {}

        # Set trigger header if set
        hx_trigger.update(
            {"triggerToast": {"message": self.get_toast_success_message(), "type": "text-bg-success bg-gradient"}}
        )
        response["HX-Trigger-After-Settle"] = json.dumps(hx_trigger)

        # Return augmented response
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)

        # Set trigger header if set
        hx_trigger = {"triggerToast": {"message": self.get_toast_error_message(), "type": "text-bg-danger bg-gradient"}}

        response["HX-Trigger-After-Settle"] = json.dumps(hx_trigger)

        return response

    # -------------- GETTER METHODS --------------

    def get_hx_trigger(self):
        """
        Getter for "hx_trigger" to be able to work with dynamic data
        """
        return self.hx_trigger

    def get_toast_success_message(self):
        """
        Getter for "toast_success_message" to be able to work with dynamic data
        """
        return self.toast_success_message

    def get_toast_error_message(self):
        """
        Getter for "toast_error_message" to be able to work with dynamic data
        """
        return self.toast_error_message

    def get_response(self):
        """
        Method, to allow overwriting the response type
        """
        return HttpResponse(HttpStatus.HTTP_200_OK)
