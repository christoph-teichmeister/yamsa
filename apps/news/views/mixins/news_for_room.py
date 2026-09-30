from django.db.models import QuerySet

from apps.news.models import News


class NewsForRoomMixin:
    """Scope the news feed to the current room."""

    def get_base_queryset(self) -> QuerySet:
        return News.objects.filter(room=self.request.room)

    def get_feed_queryset(self) -> QuerySet:
        return self.get_base_queryset().exclude(highlighted=True).order_by("-id")
