from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.account.models import User
from apps.core import htmx
from apps.transaction.models import ChildTransaction


class ChildTransactionCreateView(htmx.FormHtmxResponseMixin, generic.CreateView):
    template_name = "transaction/child_transaction_create.html"

    model = ChildTransaction
    fields = ("parent_transaction", "paid_for", "value")

    @context
    @cached_property
    def room_users(self):
        return User.objects.filter(room=self.request.room)
