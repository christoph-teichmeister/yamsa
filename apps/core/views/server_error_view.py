from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic


class ServerErrorView(generic.View):
    """Handle a 500 without re-crashing.

    Django's default handler500 renders without a request (deliberately, in case the failure came
    from request-dependent code), but 500.html extends core/base.html which needs `request` in
    every context processor it pulls in — omitting it re-raised VariableDoesNotExist on top of the
    original error.

    An htmx request never swaps in a non-2xx response, so rendering the full page here would only
    be thrown away — `htmx:afterRequest` (apps/templates/shared_partials/toast.html) already shows
    a generic error toast on any unsuccessful request, so htmx stays on the current page.

    Overrides dispatch() instead of get()/post(): the crashed request can carry any HTTP method,
    and handler500 always needs the same response regardless of it.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get("HX-Request"):
            return HttpResponse(status=500)
        return render(request, "500.html", status=500)


# handler500 (apps/config/urls.py) must be a plain request -> response callable, not a class —
# .as_view() gives it that callable.
server_error_view = ServerErrorView.as_view()
