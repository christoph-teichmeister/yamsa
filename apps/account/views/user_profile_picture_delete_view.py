from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.account.views.mixins.profile_sheet_response import ProfileSheetResponseMixin


class UserProfilePictureDeleteView(ProfileSheetResponseMixin, mixins.LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save(update_fields=["profile_picture"])

        if self.is_htmx_request():
            # Removing the picture happens mid-edit, so the sheet swaps back in still unlocked.
            return self.render_profile_sheet(user, is_editing=True)

        redirect_url = reverse("account:update", kwargs={"pk": user.id})
        return HttpResponseRedirect(redirect_url)
