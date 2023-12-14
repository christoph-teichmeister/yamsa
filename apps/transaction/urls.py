from django.urls import path

from apps.room.urls import build_room_specific_paths
from apps.transaction import views

urlpatterns = [
    path("add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path(
        "htmx/delete/child-transaction/<int:pk>",
        views.ChildTransactionDeleteHTMXView.as_view(),
        name="htmx-child-transaction-delete",
    ),
    build_room_specific_paths(
        [
            path(
                "htmx/list",
                views.TransactionListHTMXView.as_view(),
                name="htmx-transaction-list",
            ),
            path(
                "htmx/detail/<int:pk>",
                views.TransactionDetailHTMXView.as_view(),
                name="htmx-transaction-detail",
            ),
            path(
                "htmx/edit/<int:pk>",
                views.TransactionEditHTMXView.as_view(),
                name="htmx-transaction-edit",
            ),
            path(
                "htmx/add/",
                views.ChildTransactionCreateView.as_view(),
                name="htmx-child-transaction-create",
            ),
            path(
                "htmx/get-add-payment-modal",
                views.GetTransactionAddModalHTMXView.as_view(),
                name="htmx-get-transaction-add-modal",
            ),
            path(
                "htmx/money-spent",
                views.MoneySpentOnRoomView.as_view(),
                name="htmx-money-spent-on-room",
            ),
        ]
    ),
]
