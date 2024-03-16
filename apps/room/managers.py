from django.db.models import Manager

from apps.room.querysets import RoomQuerySet


class RoomManager(Manager.from_queryset(RoomQuerySet)):
    """Custom Room Manager"""
