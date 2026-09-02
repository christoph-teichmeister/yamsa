from django.contrib.auth import mixins
from django.urls import reverse
from django.utils import translation
from django.views import generic

from apps.account.constants import LANGUAGE_SESSION_KEY
from apps.account.forms import EditUserForm
from apps.account.models import User


class UserUpdateView(mixins.LoginRequiredMixin, generic.UpdateView):
    template_name = "account/edit.html"
    context_object_name = "user"
    model = User
    form_class = EditUserForm

    def dispatch(self, request, *args, **kwargs):
        # A user may only ever edit their own account — the edit button in the UI is hidden for
        # every other profile, but the URL itself had no server-side check to back that up.
        if request.user.id != kwargs["pk"]:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(viewname="account:detail", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user == self.object:
            language_value = self.object.language
            if language_value:
                translation.activate(language_value)
                self.request.session[LANGUAGE_SESSION_KEY] = language_value
            else:
                self.request.session.pop(LANGUAGE_SESSION_KEY, None)
        return response
