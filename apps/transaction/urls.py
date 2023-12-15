from django.urls import path

from apps.room.urls import build_room_specific_paths
from apps.transaction import views

urlpatterns = [
    path(
        "htmx/delete/child-transaction/<int:pk>",
        views.ChildTransactionDeleteHTMXView.as_view(),
        name="htmx-child-transaction-delete",
    ),
    build_room_specific_paths(
        [
            path(
                "add/",
                views.TransactionCreateView.as_view(),
                name="transaction-create",
            ),
            path(
                "list",
                views.TransactionListView.as_view(),
                name="transaction-list",
            ),
            path(
                "detail/<int:pk>",
                views.TransactionDetailHTMXView.as_view(),
                name="transaction-detail",
            ),
            path(
                "edit/<int:pk>",
                views.TransactionEditHTMXView.as_view(),
                name="transaction-edit",
            ),
            path(
                "add/",
                views.ChildTransactionCreateView.as_view(),
                name="child-transaction-create",
            ),
            path(
                "money-spent",
                views.MoneySpentOnRoomView.as_view(),
                name="money-spent-on-room",
            ),
        ]
    ),
]
