from apps.room.admin.user_connection_to_room_admin.user_connection_to_room_inline_base import (
    UserConnectionToRoomInlineBase,
)


class UserConnectionToRoomForRoomAdminInline(UserConnectionToRoomInlineBase):
    fk_name = "room"
