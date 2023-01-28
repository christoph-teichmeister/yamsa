from django.views import generic

from apps.account.models import User


class UserProfileView(generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User
