from django.urls import path

from apps.account import views
from apps.room.urls import build_room_specific_paths

app_name = "account"
urlpatterns = [
    path("", views.AccountRootRedirectView.as_view(), name="index"),
    path("detail/<int:pk>", views.UserDetailView.as_view(), name="detail"),
    path("update/<int:pk>/", views.UserUpdateView.as_view(), name="update"),
    path("change-password/<int:pk>/", views.UserChangePasswordView.as_view(), name="change-password"),
    path("guest/login/", views.AuthenticateGuestUserView.as_view(), name="guest-login"),
    path("register/", views.RegisterUserView.as_view(), name="register"),
    path("login/", views.LogInUserView.as_view(), name="login"),
    path("logout/", views.LogOutUserView.as_view(), name="logout"),
    path("forgot-password/", views.UserForgotPasswordView.as_view(), name="forgot-password"),
    build_room_specific_paths(
        [
            path("list", views.UserListForRoomView.as_view(), name="list"),
            path("guest/create/", views.GuestCreateView.as_view(), name="guest-create"),
            path(
                "guest/<int:pk>/send-invite-email/",
                views.GuestSendInvitationEmailView.as_view(),
                name="guest-send-invitation-email",
            ),
            path("remove-from-room/<int:pk>/", views.UserRemoveFromRoomView.as_view(), name="remove-from-room"),
        ]
    ),
]
