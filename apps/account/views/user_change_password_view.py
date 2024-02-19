from django.contrib.auth import mixins, login
from django.urls import reverse
from django.views import generic

from apps.account.forms.change_password_form import ChangePasswordForm
from apps.account.models import User


class UserChangePasswordView(mixins.LoginRequiredMixin, generic.UpdateView):
    template_name = "account/change_password.html"
    context_object_name = "user"
    model = User
    form_class = ChangePasswordForm

    def get_success_url(self):
        return reverse(viewname="account:detail", kwargs={"pk": self.request.user.id})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    def form_valid(self, form):
        super_form_valid = super().form_valid(form)
        login(request=self.request, user=form.instance)
        return super_form_valid
