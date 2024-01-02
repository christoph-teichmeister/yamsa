from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic


class LogOutUserView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        logout(request=request)
        return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))
