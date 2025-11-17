from django.contrib.auth import mixins
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View


class UserProfilePictureDeleteView(mixins.LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save(update_fields=["profile_picture"])

        redirect_url = reverse("account:update", kwargs={"pk": user.id})
        return HttpResponseRedirect(redirect_url)
