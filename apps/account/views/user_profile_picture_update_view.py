from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.account.forms import ProfilePictureForm
from apps.account.views.mixins.profile_partial_response import ProfilePartialResponseMixin


class UserProfilePictureUpdateView(ProfilePartialResponseMixin, mixins.LoginRequiredMixin, View):
    """Upload a new avatar on its own, without saving the rest of the profile."""

    def post(self, request, *args, **kwargs):
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)

        if not form.is_valid():
            if self.is_htmx_request():
                # Keep the dialog open, or the viewer never sees why the file was rejected.
                return self.render_profile_photo(request.user, picture_form=form, dialog_is_open=True)
            return HttpResponseRedirect(reverse("account:detail", kwargs={"pk": request.user.id}))

        form.save()

        if self.is_htmx_request():
            return self.render_profile_photo(request.user)

        return HttpResponseRedirect(reverse("account:detail", kwargs={"pk": request.user.id}))
