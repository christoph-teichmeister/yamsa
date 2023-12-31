from django.urls import reverse
from django.views import generic

from apps.account.forms.guest_send_invitation_form import GuestSendInvitationEmailForm
from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.core.event_loop.runner import handle_message


class GuestSendInvitationEmailView(AccountBaseContext, generic.UpdateView):
    model = User
    template_name = "account/invite_guest.html"
    form_class = GuestSendInvitationEmailForm
    context_object_name = "user"

    def form_valid(self, form):
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

    def get_success_url(self):
        return reverse(viewname="account-list", kwargs={"room_slug": self.request.room.slug})
