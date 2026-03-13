from apps.room.admin.user_connection_to_room_admin.user_connection_to_room_inline_base import (
    UserConnectionToRoomInlineBase,
)


class UserConnectionToRoomForUserAdminInline(UserConnectionToRoomInlineBase):
    fk_name = "user"
