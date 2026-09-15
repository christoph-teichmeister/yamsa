from apps.news.models import News


class NewsForRoomMixin:
    """Scope the news feed to the current room."""

    def get_base_queryset(self):
        return News.objects.filter(room=self.request.room)

    def get_feed_queryset(self):
        return self.get_base_queryset().exclude(highlighted=True).order_by("-id")
