from django.db.models import Q
from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.transaction.models import ParentTransaction


class DebtListView(DebtBaseContext, generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/list.html"

    @context
    @property
    def has_transactions(self):
        return ParentTransaction.objects.filter(room_id=self.request.room.id).exists()

    @context
    @property
    def active_debt_count(self):
        return self.model.objects.filter(room_id=self.request.room.id, settled=False).count()

    def get_queryset(self):
        # Each row phrases the debt from the viewer's side ("You owe X" / "X owes you"), so both
        # sides are resolved once in SQL rather than per row in the template.
        viewer_id = self.request.user.id
        return (
            self.model.objects.filter(room_id=self.request.room.id)
            .select_related("debitor", "creditor", "currency")
            .annotate(
                viewer_is_debitor=Q(debitor_id=viewer_id),
                viewer_is_creditor=Q(creditor_id=viewer_id),
            )
            .order_by("settled", "currency__sign", "debitor__name")
        )
