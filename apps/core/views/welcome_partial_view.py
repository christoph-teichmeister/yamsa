from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))
        return super().get(request, *args, **kwargs)
