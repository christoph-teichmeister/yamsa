from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from passkeys.models import UserPasskey


class PasskeyDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        qs = UserPasskey.objects.filter(id=request.POST.get("id"), user=request.user)
        if not qs.exists():
            return HttpResponse("Fehler: Passkey nicht gefunden oder gehört nicht dir.", status=403)
        qs.delete()
        return redirect("account:security", pk=request.user.id)
