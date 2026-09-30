from django.contrib.admin.filters import SimpleListFilter
from django.db.models import QuerySet

from apps.room.models import Room


class OpenRoomFilter(SimpleListFilter):
    title = "Open Room"
    parameter_name = "open_room"

    def lookups(self, request, model_admin) -> list[tuple[str, str]]:
        return [(room.name, room.name) for room in Room.objects.filter_status_open()]

    def queryset(self, request, queryset) -> QuerySet:
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.OPEN)
        return queryset
