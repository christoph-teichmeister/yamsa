from django.contrib.auth import mixins
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.account.models import User
from apps.config import settings


class UserDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User
