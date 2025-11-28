from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.account.constants import SESSION_TTL_SESSION_KEY


class LogOutUserView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        self._clear_session_ttl(request=request)
        logout(request=request)
        return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))

    def _clear_session_ttl(self, *, request):
        request.session.pop(SESSION_TTL_SESSION_KEY, None)
