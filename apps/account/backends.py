from passkeys.backend import PasskeyModelBackend
from passkeys.FIDO2 import auth_complete


class YamsaPasskeyBackend(PasskeyModelBackend):
    """Wraps PasskeyModelBackend but returns None instead of raising when passkeys is not in POST.

    The upstream backend raises an exception when request.POST has no 'passkeys' key,
    which breaks any authenticate() call that doesn't come from the login form
    (e.g. client.login() in tests, admin login, or management commands).
    """

    def authenticate(self, request, username="", password="", **kwargs):
        if username != "" and password != "":
            # Regular password branch — let the parent handle it (sets session["passkey"]).
            return super().authenticate(request, username=username, password=password, **kwargs)

        if request is None:
            return None

        passkeys = request.POST.get("passkeys")
        if passkeys is None:
            # No passkeys field in POST — gracefully skip instead of raising.
            return None
        if passkeys != "":
            return auth_complete(request)
        return None
