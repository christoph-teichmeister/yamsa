from django.urls import path

from apps.account import views

urlpatterns = [
    path(
        "profile/<int:pk>", views.UserProfileView.as_view(), name="account-user-profile"
    ),
    path(
        "guest_user/authenticate/",
        views.AuthenticateGuestUserView.as_view(),
        name="account-authenticate-guest-user",
    ),
    path(
        "login/",
        views.LogInUserView.as_view(),
        name="account-user-login",
    ),
    path(
        "logout/",
        views.LogOutUserView.as_view(),
        name="account-user-logout",
    ),
]
