from django.urls import path

from apps.transaction import views

urlpatterns = [
    path("add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path(
        "htmx/<str:slug>/list",
        views.TransactionListHTMXView.as_view(),
        name="htmx-transaction-list",
    ),
]
