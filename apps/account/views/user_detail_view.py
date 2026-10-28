import json

from django.contrib.auth import mixins
from django.http import HttpRequest, HttpResponse
from django.views import generic

from apps.account.forms import EditUserForm
from apps.account.models import User


class UserDetailView(mixins.LoginRequiredMixin, generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # A superuser may see all profiles. Everyone else may only see their own profile or the profiles of users
        # they share a room with. The check runs before the profile is loaded, so an unknown pk is not told apart.
        may_see_profile = (
            request.user.is_superuser
            or request.user.id == kwargs["pk"]
            or User.objects.filter(pk=kwargs["pk"], rooms__in=request.user.rooms.all()).exists()
        )
        if not may_see_profile:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        if self.request.user.id == self.object.id:
            # Own profile: every value is rendered as its own form control, editable right away.
            context["form"] = EditUserForm(instance=self.object)
        return context

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        response["HX-Trigger"] = json.dumps(
            {"notificationsEnabled": self.object.wants_to_receive_webpush_notifications}
        )
        return response
