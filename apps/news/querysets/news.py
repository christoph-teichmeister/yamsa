from django.db import models

from apps.account.models import User


class NewsQuerySet(models.QuerySet):
    """Custom implementation of QuerySet"""

    def visible_for(self, user: User):
        return self.filter(room_id__in=user.room_set.values_list("id", flat=True))
