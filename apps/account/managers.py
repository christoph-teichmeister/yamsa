from django.contrib.auth.models import UserManager as DjangoUserManager

from apps.account.querysets import UserQuerySet


class UserManager(DjangoUserManager):
    _queryset_class = UserQuerySet
