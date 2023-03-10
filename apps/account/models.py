from ai_django_core.models import CommonInfo
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(CommonInfo, AbstractUser):
    name = models.CharField(max_length=50)
    rooms = models.ManyToManyField("room.Room", through="room.UserConnectionToRoom")

    is_guest = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_guest and not self.is_superuser:
            self.username = f"{self.name}-{self.id}"
            self.email = f"{self.username}@local.local"

        super().clean()
