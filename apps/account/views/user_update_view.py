from django.conf import settings
from django.contrib.auth import mixins
from django.urls import reverse
from django.views import generic
from django_context_decorator import context
from functools import cached_property

from apps.account.forms import EditUserForm
from apps.account.models import User


class UserUpdateView(mixins.LoginRequiredMixin, generic.UpdateView):
    template_name = "account/edit.html"
    context_object_name = "user"
    model = User
    form_class = EditUserForm

    @context
    @cached_property
    def PROJECT_BASE_URL(self):
        return settings.PROJECT_BASE_URL

    @context
    @cached_property
    def DJANGO_ADMIN_SUB_URL(self):
        return settings.DJANGO_ADMIN_SUB_URL

    def get_success_url(self):
        return reverse(viewname="account-user-detail", kwargs={"pk": self.request.user.id})
