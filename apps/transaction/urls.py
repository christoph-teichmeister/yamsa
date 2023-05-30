from django.urls import path
from django.views.decorators.cache import cache_page

from apps.transaction import views

urlpatterns = [
    path("add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path(
        "htmx/<str:slug>/list",
        cache_page(60 * 60)(views.TransactionListHTMXView.as_view()),
        name="htmx-transaction-list",
    ),
]
