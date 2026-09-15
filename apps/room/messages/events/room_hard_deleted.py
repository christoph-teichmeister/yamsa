from dataclasses import dataclass

from apps.core.event_loop.messages import Event


class RoomHardDeleted(Event):
    """Named to not match `EmitModelCreatedEventOnSaveMixin`'s "RoomDeleted" convention.

    That mixin fires an auto-discovered event of exactly that name straight after
    `Room.delete()`, carrying only `instance` - too late and too little for what the
    notification and the receipt cleanup below both need.
    """

    @dataclass
    class Context:
        room_name: str
        actor_name: str
        # The room (and its members) are already gone by the time this fires, so recipients
        # travel as plain ids rather than as `User` instances the caller might be tempted to
        # re-save.
        member_user_ids: list[int]
        # (storage, name) pairs captured before the room's receipts were cascaded away - a
        # cascade only removes the DB row, never the file it points at.
        receipt_storage_refs: list[tuple]
