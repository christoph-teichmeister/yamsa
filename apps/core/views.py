import json
import time

from django.conf import settings
from django import forms
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_context_decorator import context

from apps.core.forms.push_information import PushInformationForm
from apps.core.models.push_information import PushInformation
from apps.news.models import News


class BaseView(generic.TemplateView):
    template_name = "core/base.html"

    def get(self, request, *args, **kwargs):
        return redirect(reverse(viewname="core-welcome"))


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def _get_news_base_qs(self):
        if self.request.user.is_authenticated:
            return News.objects.filter(
                room_id__in=self.request.user.room_set.values_list("id", flat=True)
            ).prefetch_related("comments")

        return News.objects.none()

    @context
    @property
    def news(self):
        return self._get_news_base_qs().exclude(highlighted=True)

    @context
    @property
    def highlighted_news(self):
        ret = self._get_news_base_qs().filter(highlighted=True).first()
        return ret


class MaintenanceOrOfflineView(generic.TemplateView):
    template_name = "core/_maintenance_or_offline.html"

    @context
    @property
    def is_in_maintenance(self):
        return settings.MAINTENANCE

    @context
    @property
    def called_by_get_user_offline_template_view(self):
        return isinstance(self, GetUserOfflineTemplateView)


class MaintenanceView(MaintenanceOrOfflineView):
    """Maintenance View is automatically injected as '' parent-url if settings.MAINTENANCE is true"""

    pass


class GetUserOfflineTemplateView(MaintenanceOrOfflineView):
    pass


class ManifestView(generic.View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(data=settings.MANIFEST)


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/javascript"


class ToastHTMXView(generic.TemplateView):
    template_name = "shared_partials/toast.html"

    @context
    @property
    def toast_id(self):
        return time.time()

    @context
    @property
    def toast_message(self):
        return self.request.GET.get("toast_message")

    @context
    @property
    def toast_type(self):
        # TODO CT: Extract these to some constant
        toast_type = self.request.GET.get("toast_type", "info")

        toast_type_dict = {
            "info": "text-bg-primary bg-gradient",
            "success": "text-bg-success bg-gradient",
            "warning": "text-bg-warning bg-gradient",
            "error": "text-bg-danger bg-gradient",
        }
        return toast_type_dict.get(toast_type)


class WebPushSaveView(generic.CreateView):
    model = PushInformation
    form_class = PushInformationForm

    def get_form_kwargs(self):
        post_data = json.loads(self.request.body.decode("utf-8"))

        subscription_data = post_data.pop("subscription", {})
        # As our database saves the auth and p256dh key in separate field,
        # we need to refactor it and insert the auth and p256dh keys in the same dictionary
        post_data.update(subscription_data.get("keys", {}))
        post_data["endpoint"] = subscription_data.get("endpoint", {})

        return {**super().get_form_kwargs(), "data": post_data}

    def form_valid(self, form):
        # Get the cleaned data in order to get status_type and group_name
        web_push_data = self.form_class.cleaned_data
        status_type = web_push_data.pop("status_type")

        # We at least need the user or group to subscribe for a notification
        if self.request.user.is_authenticated:
            # Save the subscription info with subscription data
            # as the subscription data is a dictionary and its valid
            self.form_class.save_or_delete(user=self.request.user, status_type=status_type)

            # If subscribe is made, means object is created. So return 201
            if status_type == "subscribe":
                return HttpResponse(status=201)
            # Unsubscribe is made, means object is deleted. So return 202
            elif "unsubscribe":
                return HttpResponse(status=202)
        # return super().form_valid(form)


@require_POST
@csrf_exempt
def save_info(request):
    # Parse the  json object from post data. return 400 if the json encoding is wrong
    try:
        post_data = json.loads(request.body.decode("utf-8"))
    except ValueError:
        return HttpResponse(status=400)

    subscription_data = post_data.pop("subscription", {})
    # As our database saves the auth and p256dh key in separate field,
    # we need to refactor it and insert the auth and p256dh keys in the same dictionary
    post_data.update(subscription_data.get("keys", {}))
    post_data["endpoint"] = subscription_data.get("endpoint", {})

    # pass the data through WebPushForm for validation purpose
    web_push_form = WebPushForm(post_data)

    # Check if subscriptioninfo and the web push info bot are valid
    if web_push_form.is_valid():
        # Get the cleaned data in order to get status_type and group_name
        web_push_data = web_push_form.cleaned_data
        status_type = web_push_data.pop("status_type")

        # We at least need the user or group to subscribe for a notification
        if request.user.is_authenticated:
            # Save the subscription info with subscription data
            # as the subscription data is a dictionary and its valid
            web_push_form.save_or_delete(user=request.user, status_type=status_type)

            # If subscribe is made, means object is created. So return 201
            if status_type == "subscribe":
                return HttpResponse(status=201)
            # Unsubscribe is made, means object is deleted. So return 202
            elif "unsubscribe":
                return HttpResponse(status=202)

    return HttpResponse(status=400)
