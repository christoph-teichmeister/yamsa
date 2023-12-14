from django.views import generic


class GetTransactionAddModalHTMXView(generic.TemplateView):
    template_name = "transaction/partials/transaction_add_modal.html"
