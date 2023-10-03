from django.urls import path

from apps.debt import views

urlpatterns = [
    path("settle/<int:pk>/", views.DebtSettleView.as_view(), name="transaction-settle"),
]
