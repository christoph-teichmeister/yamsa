from django.contrib.auth import mixins
from django.http import HttpResponseBadRequest
from django.views import generic

from apps.account.models import User, UserFriendship
from apps.room.services.suggested_guest_service import SuggestedGuestService


class SuggestedGuestFriendToggleHTMXView(mixins.LoginRequiredMixin, generic.TemplateView):
    template_name = "room/_suggested_guest_list.html"

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("suggested_user_id")

        if not user_id:
            return HttpResponseBadRequest("Missing suggested user selection.")

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponseBadRequest("Suggested user not found.")

        if target_user == request.user or target_user.is_guest:
            return HttpResponseBadRequest("Cannot toggle friendship for this user.")

        friendship = UserFriendship.objects.filter(user=request.user, friend=target_user).first()

        if friendship:
            friendship.delete()
        else:
            UserFriendship.objects.create(user=request.user, friend=target_user)

        suggested_guests = SuggestedGuestService(user=request.user).get_suggested_guests()
        suggested_guest_context = request.POST.get("suggested_guest_context", "create")
        add_inline_form = suggested_guest_context == "existing"
        context = self.get_context_data(
            suggested_guests=suggested_guests,
            suggested_guest_context=suggested_guest_context,
            add_inline_form=add_inline_form,
            add_inline_form_action_url=request.POST.get("suggested_guest_action_url", ""),
            add_inline_room_slug=request.POST.get("suggested_guest_room_slug", ""),
        )

        return self.render_to_response(context)
