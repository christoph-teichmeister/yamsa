from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.account.forms.guest_send_invitation_form import GuestSendInvitationEmailForm
from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin


class GuestSendInvitationEmailView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, AccountBaseContext, generic.UpdateView
):
    model = User
    template_name = "account/invite_guest.html"
    form_class = GuestSendInvitationEmailForm
    context_object_name = "user"

    def get_queryset(self) -> QuerySet:
        return User.objects.filter(is_guest=True, rooms=self.request.room)

    def form_valid(self, form: GuestSendInvitationEmailForm) -> HttpResponse:
        # The button is hidden while the window runs, but a replayed POST must not mail again.
        guest = self.get_queryset().annotate_invitation_email_can_be_sent().get(pk=self.object.pk)
        if not guest.invitation_email_can_be_sent:
            form.add_error("email", _("An invitation was sent a moment ago. Please wait a few minutes."))
            return self.form_invalid(form)

        form_valid = super().form_valid(form)

        handle_message(
            SendInvitationEmail(
                context_data={
                    "invitee": self.object,
                    "invitee_email": form.cleaned_data["email"],
                    "inviter": self.request.user,
                }
            )
        )

        return form_valid

    def get_success_url(self) -> str:
        return reverse(viewname="account:list", kwargs={"room_slug": self.request.room.slug})
