from django.contrib.admin import ModelAdmin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.room.models import Room


class OpenRoomFilter(SimpleListFilter):
    title = "Open Room"
    parameter_name = "open_room"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> list[tuple[str, str]]:
        return [(room.name, room.name) for room in Room.objects.filter_status_open()]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> list[tuple[str, str]]:
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.OPEN)
        return queryset
