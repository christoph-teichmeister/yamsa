from django.contrib.admin.filters import SimpleListFilter

from apps.room.models import Room


class ClosedRoomFilter(SimpleListFilter):
    title = "Closed Room"
    parameter_name = "closed_room"

    def lookups(self, request, model_admin):
        return [(room.name, room.name) for room in Room.objects.filter_status_closed()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.CLOSED)
        return queryset
