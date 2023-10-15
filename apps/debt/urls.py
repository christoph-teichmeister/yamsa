from django.urls import path

from debt.views.debt_settle_view import DebtSettleView

urlpatterns = [
    path("settle/<int:pk>/", DebtSettleView.as_view(), name="transaction-settle"),
]
