from django.urls import path

from apps.account import views

urlpatterns = [
    path(
        "profile/<int:pk>", views.UserProfileView.as_view(), name="account-user-profile"
    ),
]
