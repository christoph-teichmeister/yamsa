import time

from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.news.models import News


class BaseView(generic.TemplateView):
    template_name = "core/base.html"

    def get(self, request, *args, **kwargs):
        return redirect(reverse(viewname="core-welcome"))


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        news_qs = News.objects.all().prefetch_related("comments")

        context_data["news"] = news_qs.exclude(highlighted=True)
        context_data["highlighted_news"] = news_qs.filter(highlighted=True).first()
        return context_data


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
        toast_type = self.request.GET.get("toast_type", "info")

        toast_type_dict = {
            "info": "text-bg-primary bg-gradient",
            "success": "text-bg-success bg-gradient",
            "warning": "text-bg-warning bg-gradient",
            "error": "text-bg-danger bg-gradient",
        }
        return toast_type_dict.get(toast_type)
