from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic


class BaseView(generic.TemplateView):
    template_name = "core/base.html"

    def get(self, request, *args, **kwargs):
        return redirect(reverse(viewname="core:welcome"))
