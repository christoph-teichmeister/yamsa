import http
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views import generic

from apps.webpush.forms.web_push_information import WebPushInformationForm
from apps.webpush.models.web_push_information import WebpushInformation


class WebPushSaveView(LoginRequiredMixin, generic.CreateView):
    raise_exception = True
    model = WebpushInformation
    form_class = WebPushInformationForm
    template_name = ""

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        try:
            post_data = json.loads(request.body.decode("utf-8"))
        except ValueError:
            return HttpResponse(status=http.HTTPStatus.BAD_REQUEST, content="Invalid JSON body")

        subscription_data = post_data.get("subscription", {}) if isinstance(post_data, dict) else None
        if not isinstance(subscription_data, dict) or not isinstance(subscription_data.get("keys", {}), dict):
            return HttpResponse(status=http.HTTPStatus.BAD_REQUEST, content="Invalid subscription payload")

        self.post_data = post_data
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict:
        post_data = {k: v for k, v in self.post_data.items() if k != "subscription"}
        subscription_data = self.post_data.get("subscription", {})

        return {
            **super().get_form_kwargs(),
            "data": {
                **post_data,
                "endpoint": subscription_data.get("endpoint", ""),
                **subscription_data.get("keys", {}),
                # Set last: the account always comes from the session, never from the request body.
                "user": self.request.user,
            },
        }

    def form_valid(self, form: WebPushInformationForm) -> HttpResponse:
        status_type = form.cleaned_data.get("status_type")

        # Save the subscription info with subscription data as the subscription data is a dictionary and its valid
        form.save_or_delete()
        if status_type == "subscribe":
            # If subscribe was passed, that means object is created, so return 201
            return HttpResponse(status=http.HTTPStatus.CREATED)
        if status_type == "unsubscribe":
            # If unsubscribe was passed, that means the object was deleted, so return 202
            return HttpResponse(status=http.HTTPStatus.ACCEPTED)

        return HttpResponse(
            status=http.HTTPStatus.BAD_REQUEST,
            content="Unknown status_type",
        )

    def form_invalid(self, form: WebPushInformationForm) -> HttpResponse:
        return HttpResponse(status=http.HTTPStatus.BAD_REQUEST, content=form.errors)
