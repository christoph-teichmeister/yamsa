from model_bakery import seq
from model_bakery.recipe import Recipe

from apps.account.models import User

default_password = "Admin123$"
default_password_hashed = "pbkdf2_sha256$390000$spnzZngacBx7WjSs7WGucD$vSfEn1OcGbBHjNdvDbn/HyhHQb9PtZuwilh4+abKOE8="

base_user_data = {
    "is_superuser": False,
    "is_staff": False,
    "is_active": True,
}

guest_user = Recipe(
    User,
    name=seq("Guest User "),
    password=default_password_hashed,
    username=seq("guest-user-"),
    email=seq("guest-user-", suffix="@yamsa.local"),
    is_guest=True,
    **base_user_data
)

user = Recipe(
    User,
    name=seq("User "),
    password=default_password_hashed,
    username=seq("user-"),
    email=seq("user-", suffix="@yamsa.local"),
    is_guest=False,
    **base_user_data
)

superuser = Recipe(
    User,
    name=seq("Superuser "),
    password=default_password_hashed,
    username=seq("superuser-"),
    email=seq("superuser-", suffix="@yamsa.local"),
    is_guest=False,
    is_superuser=True,
    is_staff=True,
    is_active=True,
)
