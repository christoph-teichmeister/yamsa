from django.http import HttpRequest

from apps.currency.models import Currency


def currency_context(request: HttpRequest):
    return {"all_currencies": Currency.objects.all()}
