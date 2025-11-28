from django.conf import settings

from apps.account.constants import SESSION_TTL_SESSION_KEY


class SessionKeepAliveMiddleware:
    """Refresh authenticated sessions while ignoring safe HTMX heartbeats."""

    SKIP_KEYWORDS = ("heartbeat", "reminder", "keepalive")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._refresh_session_if_needed(request)
        return self.get_response(request)

    def _refresh_session_if_needed(self, request):
        if not self._should_refresh(request):
            return

        target_ttl = request.session.get(SESSION_TTL_SESSION_KEY) or settings.SESSION_COOKIE_AGE
        if not isinstance(target_ttl, int) or target_ttl <= 0:
            return

        request.session.set_expiry(target_ttl)

    def _should_refresh(self, request) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        if not hasattr(request, "session"):
            return False

        return not self._is_safe_htmx_fragment(request)

    def _is_safe_htmx_fragment(self, request) -> bool:
        if not request.headers.get("HX-Request"):
            return False

        lower_path = (request.path or "").lower()
        if any(keyword in lower_path for keyword in self.SKIP_KEYWORDS):
            return True

        header_values = " ".join(
            filter(None, (request.headers.get("HX-Trigger"), request.headers.get("HX-Trigger-After-Settle")))
        ).lower()
        return any(keyword in header_values for keyword in self.SKIP_KEYWORDS)
