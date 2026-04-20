from django.contrib.admin.filters import SimpleListFilter

from apps.room.models import Room


class OpenRoomFilter(SimpleListFilter):
    title = "Open Room"
    parameter_name = "open_room"

    def lookups(self, request, model_admin):
        return [(room.name, room.name) for room in Room.objects.open()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.OPEN)
        return queryset
