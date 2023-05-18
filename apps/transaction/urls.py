from django.urls import path

from apps.transaction import views

urlpatterns = [
    path("add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path(
        "<int:pk>/settle/",
        views.TransactionSettleView.as_view(),
        name="transaction-settle",
    ),
]
