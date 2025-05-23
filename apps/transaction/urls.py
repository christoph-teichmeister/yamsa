from django.urls import path

from apps.room.urls import build_room_specific_paths
from apps.transaction import views

app_name = "transaction"
urlpatterns = [
    build_room_specific_paths(
        [
            path(
                "add/",
                views.TransactionCreateView.as_view(),
                name="create",
            ),
            path(
                "list",
                views.TransactionListView.as_view(),
                name="list",
            ),
            path(
                "detail/<int:pk>",
                views.TransactionDetailView.as_view(),
                name="detail",
            ),
            path(
                "edit/<int:pk>",
                views.TransactionEditView.as_view(),
                name="edit",
            ),
            path(
                "child-transaction/add/",
                views.ChildTransactionCreateView.as_view(),
                name="child-transaction-create",
            ),
            path(
                "child-transaction/delete/<int:pk>",
                views.ChildTransactionDeleteView.as_view(),
                name="child-transaction-delete",
            ),
            path(
                "parent-transaction/delete/<int:pk>",
                views.ParentTransactionDeleteView.as_view(),
                name="parent-transaction-delete",
            ),
        ]
    ),
]
