from django.urls import path

from apps.debt.views.debt_settle_view import DebtSettleView
from apps.debt.views.htmx_views.debt_list_view import DebtListView
from apps.room.urls import build_room_specific_paths

urlpatterns = [
    build_room_specific_paths(
        [
            path(
                "list",
                DebtListView.as_view(),
                name="debt-list",
            ),
            path(
                "settle/<int:pk>/",
                DebtSettleView.as_view(),
                name="debt-settle",
            ),
        ]
    ),
]
