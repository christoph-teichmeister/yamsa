from django.contrib.auth import mixins
from django.views import generic

from apps.account.models import User


class UserDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User

    def dispatch(self, request, *args, **kwargs):
        if not (
            request.user.is_superuser
            or request.user.rooms.filter(id__in=self.get_object().rooms.values_list("id", flat=True))
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
