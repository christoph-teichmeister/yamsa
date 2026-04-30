from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from passkeys.models import UserPasskey

from apps.account.models import User


class UserSecurityView(LoginRequiredMixin, generic.DetailView):
    template_name = "account/security.html"
    context_object_name = "user"
    model = User

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.id != kwargs["pk"]:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        passkey = UserPasskey.objects.filter(user=self.object).first()
        context["passkey"] = passkey
        context["has_passkey"] = passkey is not None
        return context
