from functools import cached_property

from django.conf import settings
from django.contrib.auth import mixins
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.account.forms import EditUserForm
from apps.account.models import User


class UserUpdateView(mixins.LoginRequiredMixin, generic.UpdateView):
    template_name = "account/edit.html"
    context_object_name = "user"
    model = User
    form_class = EditUserForm

    def get_success_url(self):
        return reverse(viewname="account:detail", kwargs={"pk": self.object.id})
