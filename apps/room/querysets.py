from django.db import models


class RoomQuerySet(models.QuerySet):
    def visible_for(self, user):
        if user.is_anonymous:
            return self.none()

        if user.is_superuser:
            return self.all()

        return self.filter(users=user)
