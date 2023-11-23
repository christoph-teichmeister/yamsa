from django.urls import path

from apps.debt.views.debt_settle_view import DebtSettleView
from apps.debt.views.htmx_views.debt_list_view import DebtListHTMXView
from apps.room.urls import build_room_specific_paths

urlpatterns = [
    path("settle/<int:pk>/", DebtSettleView.as_view(), name="debt-settle"),
    build_room_specific_paths([path("htmx/debt/list", DebtListHTMXView.as_view(), name="htmx-debt-list")]),
]
