from enum import IntEnum


class AttentionRank(IntEnum):
    """Order in which the dashboard surfaces a room: the lower the rank, the more it needs doing."""

    OWING = 0
    BALANCED = 1
    RECEIVING = 2
    SETTLED = 3
