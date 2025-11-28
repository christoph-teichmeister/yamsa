import http
import json

from django.http import HttpResponse
from django.views import generic

from apps.webpush.forms.web_push_information import WebPushInformationForm
from apps.webpush.models.web_push_information import WebpushInformation


class WebPushSaveView(generic.CreateView):
    model = WebpushInformation
    form_class = WebPushInformationForm
    template_name = ""

    def get_form_kwargs(self):
        post_data = json.loads(self.request.body.decode("utf-8"))

        subscription_data = post_data.pop("subscription", {})

        ret = {
            **super().get_form_kwargs(),
            "data": {
                "endpoint": subscription_data.get("endpoint", {}),
                "user": self.request.user,
                **subscription_data.get("keys", {}),
                **post_data,
            },
        }

        return ret

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            return HttpResponse(status=http.HTTPStatus.BAD_REQUEST)

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

    def form_invalid(self, form):
        return HttpResponse(status=http.HTTPStatus.BAD_REQUEST, content=form.errors)
