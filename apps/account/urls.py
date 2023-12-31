from django.urls import path

from apps.account import views
from apps.room.urls import build_room_specific_paths

urlpatterns = [
    path("detail/<int:pk>", views.UserDetailView.as_view(), name="account-user-detail"),
    path("update/<int:pk>/", views.UserUpdateView.as_view(), name="account-user-update"),
    path("change-password/<int:pk>/", views.UserChangePasswordView.as_view(), name="account-user-change-password"),
    path("guest_user/authenticate/", views.AuthenticateGuestUserView.as_view(), name="account-authenticate-guest-user"),
    path("register/", views.RegisterUserView.as_view(), name="account-user-register"),
    path("login/", views.LogInUserView.as_view(), name="account-user-login"),
    path("logout/", views.LogOutUserView.as_view(), name="account-user-logout"),
    build_room_specific_paths(
        [
            path(
                "list",
                views.UserListForRoomView.as_view(),
                name="account-list",
            ),
            path(
                "guest/create/",
                views.GuestCreateView.as_view(),
                name="account-create-guest",
            ),
            path(
                "guest_user/<int:pk>/send-invite-email/",
                views.GuestSendInvitationEmailView.as_view(),
                name="account-send-guest-invitation-email",
            ),
            path(
                "remove-from-room/<int:pk>/",
                views.UserRemoveFromRoomView.as_view(),
                name="account-remove-from-room",
            ),
        ]
    ),
]
