from time import time

from ambient_toolbox.models import CommonInfo
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class User(FullCleanOnSaveMixin, CommonInfo, AbstractUser):
    name = models.CharField(max_length=50)
    rooms = models.ManyToManyField("room.Room", through="room.UserConnectionToRoom")

    is_guest = models.BooleanField(default=True)

    paypal_me_username = models.CharField(max_length=100, null=True, blank=True)

    wants_to_receive_webpush_notifications = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_guest and not self.is_superuser:
            timestamp = time()
            self.username = f"{self.name}-{timestamp}"
            self.email = f"{self.username}@local.local"
            self.password = f"{self.name}-{timestamp}"

        super().clean()
