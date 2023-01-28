from django.views import generic


class BaseView(generic.TemplateView):
    template_name = "core/base.html"


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"
