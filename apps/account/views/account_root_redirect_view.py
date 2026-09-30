from django.shortcuts import redirect
from django.views import View


class AccountRootRedirectView(View):
    def get(self, request, *args: object, **kwargs: object):
        if request.user.is_authenticated:
            return redirect("account:detail", pk=request.user.pk)

        return redirect("account:login")
