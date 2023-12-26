from django.contrib.auth import mixins
from django.views import generic

from apps.account.models import User


class UserDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User
