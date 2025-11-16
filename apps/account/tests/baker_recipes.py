from model_bakery import seq
from model_bakery.recipe import Recipe

from apps.account.models import User

default_password = "Admin123$"
# Tests use django.contrib.auth.hashers.MD5PasswordHasher
default_password_hashed = "md5$JBOrgPJ8jG4q6wYGkVhIxp$327dd1d9a3cc74ff43fae52623871315"

base_user_data = {
    "is_superuser": False,
    "is_staff": False,
    "wants_to_receive_webpush_notifications": True,
    "wants_to_receive_payment_reminders": True,
}

guest_user = Recipe(
    User,
    name=seq("Guest User "),
    password=default_password_hashed,
    email=seq("guest-user-", suffix="@yamsa.local"),
    is_guest=True,
    **base_user_data,
)

user = Recipe(
    User,
    name=seq("User "),
    password=default_password_hashed,
    email=seq("user-", suffix="@yamsa.local"),
    is_guest=False,
    **base_user_data,
)

superuser = Recipe(
    User,
    name=seq("Superuser "),
    password=default_password_hashed,
    email=seq("superuser-", suffix="@yamsa.local"),
    is_guest=False,
    is_superuser=True,
    is_staff=True,
)
