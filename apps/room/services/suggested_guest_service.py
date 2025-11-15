from collections import OrderedDict, defaultdict

from apps.account.models import UserFriendship
from apps.room.dataclasses import SuggestedGuest
from apps.room.models import Room, UserConnectionToRoom


class SuggestedGuestService:
    def __init__(self, user, limit: int = 8):
        self.user = user
        self.limit = limit

    def get_suggested_guests(self) -> list[SuggestedGuest]:
        room_ids = list(Room.objects.filter(users=self.user).values_list("id", flat=True))
        if not room_ids:
            return []

        connections = (
            UserConnectionToRoom.objects.filter(room_id__in=room_ids)
            .exclude(user=self.user)
            .select_related("user")
            .order_by("-created_at")
        )

        seen_users: OrderedDict[int, UserConnectionToRoom] = OrderedDict()
        rooms_shared: defaultdict[int, set[int]] = defaultdict(set)

        for connection in connections:
            target_user = connection.user

            if target_user.is_guest:
                continue

            rooms_shared[target_user.id].add(connection.room_id)

            if target_user.id in seen_users:
                continue

            seen_users[target_user.id] = connection

            if len(seen_users) >= self.limit:
                break

        if not seen_users:
            return []

        friend_ids = set(UserFriendship.objects.filter(user=self.user).values_list("friend_id", flat=True))

        suggestions: list[SuggestedGuest] = []
        for user_id, connection in seen_users.items():
            rooms_together = max(len(rooms_shared.get(user_id, set())), 1)
            suggestions.append(
                SuggestedGuest.from_user(
                    connection.user,
                    is_friend=user_id in friend_ids,
                    rooms_together=rooms_together,
                )
            )

        friend_suggestions = [guest for guest in suggestions if guest.is_friend]
        other_suggestions = [guest for guest in suggestions if not guest.is_friend]

        return friend_suggestions + other_suggestions
