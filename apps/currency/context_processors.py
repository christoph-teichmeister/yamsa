from apps.currency.models import Currency


def currency_context(request) -> dict:
    return {"all_currencies": Currency.objects.all()}
