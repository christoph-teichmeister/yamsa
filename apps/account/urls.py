from django.urls import path

from apps.account import views

urlpatterns = [
    path("detail/<int:pk>", views.UserDetailView.as_view(), name="account-user-detail"),
    path(
        "update/<int:pk>/", views.UserUpdateView.as_view(), name="account-user-update"
    ),
    path(
        "guest_user/create/",
        views.GuestCreateView.as_view(),
        name="account-create-guest-user",
    ),
    path(
        "guest_user/authenticate/",
        views.AuthenticateGuestUserView.as_view(),
        name="account-authenticate-guest-user",
    ),
    path(
        "register/",
        views.RegisterUserView.as_view(),
        name="account-user-register",
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
    path(
        "htmx/<str:slug>/list",
        # Cached for 10 minutes
        # vary_on_headers("Cookie")(
        #     cache_page(timeout=60 * 10, key_prefix="htmx-account-list")(
        #         views.UserListForRoomHTMXView.as_view()
        #     )
        # ),
        views.UserListForRoomHTMXView.as_view(),
        name="htmx-account-list",
    ),
]
