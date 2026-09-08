from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views import generic

from apps.core.services.pwa_scope_service import resolve_scope


class PwaSessionView(generic.View):
    """What a queued submission needs to know before it may be replayed.

    The token, because the one captured with the form belongs to the session that rendered it and a
    sign-in since then has replaced the secret behind it. The scope, because cache and queue
    outlive the session: replaying one visitor's entry under the account that happens to be signed
    in now would book their expense against someone else.
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "csrf_token": get_token(request),
                "scope": resolve_scope(request.user),
            }
        )
