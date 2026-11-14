from django.urls import reverse

from apps.debt.models import Debt
from apps.room.models import Room

PUSH = "apps.webpush.utils.Notification.send_to_user"


def remind_url(debt: Debt) -> str:
    return reverse("debt:remind", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def list_url(room: Room) -> str:
    return reverse("debt:list", kwargs={"room_slug": room.slug})
