from django.urls import path

from apps.debt.views.debt_settle_view import DebtSettleView
from apps.debt.views.htmx_views.debt_list_view import DebtListHTMXView

urlpatterns = [
    path("settle/<int:pk>/", DebtSettleView.as_view(), name="debt-settle"),
    path("<str:room_slug>/htmx/debt/list", DebtListHTMXView.as_view(), name="htmx-debt-list"),
]
