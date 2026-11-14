from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.forms import RoomStatusForm
from apps.room.messages.events.room_debts_force_settled import RoomDebtsForceSettled
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room
from apps.room.views.mixins import RoomMembershipRequiredMixin
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomStatusUpdateView(RoomMembershipRequiredMixin, RoomSheetResponseMixin, RoomBaseContext, generic.UpdateView):
    # Answers with the sheet, never with a page of its own: closing a room changes its badge, its
    # readiness row and whether its fields can be edited at all, so the whole sheet comes back.
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomStatusForm

    def get_success_url(self) -> str:
        return reverse("room:detail", kwargs={"room_slug": self.object.slug})

    def get_form(self, form_class: type[RoomStatusForm] | None = None) -> RoomStatusForm:
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    def form_valid(self, form: RoomStatusForm) -> HttpResponse:
        status_changed = "status" in form.changed_data
        force_closed = form.closes_the_room and form.cleaned_data.get("force_close")
        reopened = status_changed and form.cleaned_data["status"] == Room.StatusChoices.OPEN
        affected_user_ids: list[int] = []

        # Room and debts change together: a failure half-way must not leave a closed room with open
        # debts, or settled debts in an open room. Events fire after the block, see AGENTS.md.
        with transaction.atomic():
            response = super().form_valid(form)

            if force_closed:
                open_debts = self.object.debts.filter(settled=False)
                affected_user_ids = list(
                    {user_id for pair in open_debts.values_list("debitor_id", "creditor_id") for user_id in pair}
                )
                open_debts.update(settled=True, settled_at=timezone.localdate(), force_settled_at=timezone.now())

            if reopened:
                self._release_force_settled_debts(revert=form.cleaned_data["revert_force_settled"])

        if affected_user_ids:
            handle_message(
                RoomDebtsForceSettled(
                    context_data={
                        "room": self.object,
                        "actor": self.request.user,
                        "affected_user_ids": affected_user_ids,
                    }
                )
            )

        if status_changed:
            handle_message(RoomStatusChanged(context_data={"room": self.object}))

        if not self.is_htmx_request():
            return response

        return self.render_room_sheet(self.object)

    def _release_force_settled_debts(self, *, revert: bool) -> None:
        """Drop the force marker; when reverting, also reopen exactly those debts and recompute.

        Honestly settled debts carry no marker, so they stay settled and the optimiser folds them
        back into its balances.
        """
        force_settled = self.object.debts.filter(force_settled_at__isnull=False)
        if not revert:
            force_settled.update(force_settled_at=None)
            return

        if force_settled.update(settled=False, settled_at=None, force_settled_at=None):
            DebtOptimiseService.process(room_id=self.object.id)

    def form_invalid(self, form: RoomStatusForm) -> HttpResponse:
        if self.is_htmx_request():
            return self.render_room_sheet(self.object, status_form=form)
        return super().form_invalid(form)
