from django.contrib.auth.models import UserManager as DjangoUserManager

from apps.account.querysets import UserQuerySet


class UserManager(DjangoUserManager.from_queryset(UserQuerySet)):
    """Custom Implementation of Djangos UserManager"""
