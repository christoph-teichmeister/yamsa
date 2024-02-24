from model_bakery import baker

from apps.account.handlers.commands.remove_user_from_room import handle_remove_user_from_room
from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.core.tests.setup import BaseTestSetUp


class RemoveUserFromRoomHandlerTestCase(BaseTestSetUp):
    def test_regular(self):
        room = baker.make_recipe("apps.room.tests.room")
        room.users.add(self.user)

        context = {"room": room, "user_to_be_removed": self.user, "user_requesting_removal": self.superuser}
        ret = handle_remove_user_from_room(context=RemoveUserFromRoom.Context(**context))

        self.assertIsInstance(ret, UserRemovedFromRoom)
        self.assertFalse(self.user.rooms.filter(id=room.id).exists())

        self.assertEqual(ret.Context.__dict__, context)
