from .user_connection_to_room_inline_base import UserConnectionToRoomInlineBase


class UserConnectionToRoomForRoomAdminInline(UserConnectionToRoomInlineBase):
    fk_name = "room"
