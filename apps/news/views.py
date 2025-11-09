from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from apps.news.constants import NEWS_FEED_PAGE_SIZE
from apps.news.models import News


class NewsFeedChunkView(LoginRequiredMixin, generic.TemplateView):
    template_name = "shared_partials/news_batch.html"

    def get_paginate_by(self):
        try:
            limit = int(self.request.GET.get("limit", NEWS_FEED_PAGE_SIZE))
        except (TypeError, ValueError):
            return NEWS_FEED_PAGE_SIZE
        return max(1, min(limit, 50))

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return News.objects.none()
        room_ids = self.request.user.room_set.values_list("id", flat=True)
        return News.objects.filter(room_id__in=room_ids).exclude(highlighted=True).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        cursor_value = self.request.GET.get("cursor")
        if cursor_value:
            try:
                cursor_id = int(cursor_value)
            except (TypeError, ValueError):
                cursor_id = None
            else:
                queryset = queryset.filter(id__lt=cursor_id)
        page_size = self.get_paginate_by()
        news_batch = list(queryset[:page_size])
        next_cursor = news_batch[-1].id if len(news_batch) == page_size else None
        context.update(
            {
                "news": news_batch,
                "news_next_cursor": next_cursor,
                "news_initial_render": False,
            }
        )
        return context
