from unittest.mock import Mock

from django.contrib.admin import AdminSite

from apps.account.admin import UserAdmin
from apps.account.models import User


def test_get_readonly_fields(superuser):
    expected_readonly_fields = ("created_by", "lastmodified_by", "created_at", "lastmodified_at", "last_login")

    user_admin = UserAdmin(model=User, admin_site=AdminSite())
    assert expected_readonly_fields == user_admin.get_readonly_fields(request=Mock(user=superuser))
