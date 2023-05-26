from django.urls import reverse
from django.views import generic

from apps.account.forms import EditUserForm
from apps.account.models import User


class UserUpdateView(generic.UpdateView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User
    form_class = EditUserForm

    def get_success_url(self):
        return reverse(
            viewname="account-user-detail", kwargs={"pk": self.request.user.id}
        )
