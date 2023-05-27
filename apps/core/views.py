from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.news.models import News


class BaseView(generic.TemplateView):
    template_name = "core/base.html"

    def get(self, request, *args, **kwargs):
        return redirect(reverse(viewname="core-welcome"))


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["news"] = News.objects.exclude(highlighted=True)
        context_data["highlighted_news"] = News.objects.filter(highlighted=True).first()
        return context_data
