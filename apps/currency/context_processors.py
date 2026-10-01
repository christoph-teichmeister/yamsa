from django.http import HttpRequest

from apps.currency.models import Currency


def currency_context(request: HttpRequest) -> dict:
    return {"all_currencies": Currency.objects.all()}
