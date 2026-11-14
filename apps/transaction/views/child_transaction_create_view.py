from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.account.models import User
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ChildTransactionCreateView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, TransactionBaseContext, generic.TemplateView
):
    """Serves the blank split row only. Shares are persisted by the create/edit forms, never from here."""

    template_name = "transaction/child_transaction_create.html"
    http_method_names = ("get", "head", "options")

    @context
    @cached_property
    def room_users(self) -> QuerySet:
        return User.objects.filter(room=self.request.room)
