from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.account.views.mixins.profile_partial_response import ProfilePartialResponseMixin


class UserProfilePictureDeleteView(ProfilePartialResponseMixin, mixins.LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save(update_fields=["profile_picture"])

        if self.is_htmx_request():
            return self.render_profile_photo(user)

        redirect_url = reverse("account:detail", kwargs={"pk": user.id})
        return HttpResponseRedirect(redirect_url)
