from django.urls import path

from apps.debt import views

urlpatterns = [
    path(
        "settle/",
        views.DebtSettleView.as_view(),
        name="transaction-settle",
    ),
]
