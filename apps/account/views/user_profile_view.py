from django.views import generic

from apps.account.models import User
from apps.config import settings


class UserProfileView(generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["PROJECT_BASE_URL"] = settings.PROJECT_BASE_URL
        context_data["DJANGO_ADMIN_SUB_URL"] = settings.DJANGO_ADMIN_SUB_URL
        return context_data
