from django.conf import settings
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

    def get_success_url(self):
        return reverse(viewname="account:detail", kwargs={"pk": self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user == self.object:
            language_value = self.object.language
            if language_value:
                translation.activate(language_value)
                self.request.session[LANGUAGE_SESSION_KEY] = language_value
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_value)
            else:
                self.request.session.pop(LANGUAGE_SESSION_KEY, None)
                response.delete_cookie(settings.LANGUAGE_COOKIE_NAME)
        return response
