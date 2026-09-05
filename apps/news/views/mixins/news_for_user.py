from apps.news.models import News


class NewsForUserMixin:
    """Scope the news feed to the rooms the requesting user belongs to."""

    def get_base_queryset(self):
        room_ids = self.request.user.room_set.values_list("id", flat=True)
        return News.objects.filter(room_id__in=room_ids)

    def get_feed_queryset(self):
        return self.get_base_queryset().exclude(highlighted=True).order_by("-id")
