from django.urls import path

from apps.transaction import views

urlpatterns = [
    path("add/", views.TransactionCreateView.as_view(), name="transaction-add"),
    path(
        "<str:room_slug>/htmx/list",
        # Cached for 10 minutes
        # cache_page(60 * 10)(views.TransactionListHTMXView.as_view()),
        views.TransactionListHTMXView.as_view(),
        name="htmx-transaction-list",
    ),
    path(
        "<str:room_slug>/htmx/detail/<int:pk>",
        views.TransactionDetailHTMXView.as_view(),
        name="htmx-transaction-detail",
    ),
    path("htmx/edit/<int:pk>", views.TransactionEditHTMXView.as_view(), name="htmx-transaction-edit"),
    path("htmx/add/", views.ChildTransactionCreateView.as_view(), name="htmx-child-transaction-create"),
    path(
        "htmx/delete/child-transaction/<int:pk>",
        views.ChildTransactionDeleteHTMXView.as_view(),
        name="htmx-child-transaction-delete",
    ),
    path(
        "htmx/<str:slug>/add-payment-modal",
        views.TransactionAddModalHTMXView.as_view(),
        name="htmx-transaction-add-modal",
    ),
    path("htmx/<str:slug>/money-spent", views.MoneySpentOnRoomView.as_view(), name="htmx-money-spent-on-room"),
]
