from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from passkeys.FIDO2 import reg_begin
from passkeys.models import UserPasskey


class PasskeyRegBeginView(LoginRequiredMixin, View):
    def get(self, request):
        if UserPasskey.objects.filter(user=request.user).exists():
            return JsonResponse(
                {"status": "ERR", "message": "Du hast bereits einen Passkey registriert."},
                status=400,
            )
        return reg_begin(request)
