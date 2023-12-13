from apps.currency.models import Currency


def currency_context(request):
    return {"all_currencies": Currency.objects.all()}
