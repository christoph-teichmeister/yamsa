from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import Category, ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionCreateView(TransactionBaseContext, generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "transaction/create.html"

    _active_tab = "transaction"

    def get_initial(self):
        initial = super().get_initial()
        if not initial.get("category"):
            default_category = Category.get_default_category()
            if default_category:
                initial["category"] = default_category.pk
        return initial

    def get_success_url(self):
        return reverse("transaction:list", kwargs={"room_slug": self.request.room.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("request", self.request)
        return kwargs

    def form_invalid(self, form):
        self._form_error_toast_message = self._get_toast_error_message(form)
        ret = super().form_invalid(form)
        return ret

    def _get_toast_error_message(self, form):
        non_field_errors = form.non_field_errors()
        if non_field_errors:
            return str(non_field_errors[0])
        for errors in form.errors.values():
            if errors:
                return str(errors[0])
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["current_datetime"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        context["current_datetime"] = timezone.now().strftime(r"Y-m-d\TH:i")
        context["selected_paid_for"] = self._build_selected_paid_for()

        form = context.get("form")

        context["selected_paid_by"] = self._build_selected_paid_by(form)
        context["selected_currency"] = self._build_selected_currency(form)
        context["selected_category"] = self._build_selected_category(form)
        context["form_error_toast_message"] = getattr(self, "_form_error_toast_message", None)

        return context

    def _build_selected_paid_for(self):
        if self.request.method == "POST":
            return [str(user_id) for user_id in self.request.POST.getlist("paid_for")]
        return [str(user_id) for user_id in self.request.room.users.values_list("id", flat=True)]

    def _build_selected_paid_by(self, form):
        posted = self.request.POST.get("paid_by")
        if posted:
            return posted
        if form:
            value = form["paid_by"].value()
            if value:
                return str(value)
        return str(self.request.user.id)

    def _build_selected_currency(self, form):
        if self.request.method == "POST":
            posted = self.request.POST.get("currency")
            if posted:
                return posted
        if form:
            value = form["currency"].value()
            if value:
                return str(value)
        return str(self.request.room.preferred_currency.id)

    def _build_selected_category(self, form):
        if self.request.method == "POST":
            posted = self.request.POST.get("category")
            if posted:
                return posted
        if form:
            value = form["category"].value()
            if value:
                return str(value)
        default_category = Category.get_default_category()
        if default_category:
            return str(default_category.id)
        return ""
