from functools import cached_property

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django_context_decorator import context

from apps.news.constants import NEWS_FEED_PAGE_SIZE
from apps.news.models import News


class NewsForUserMixin:
    def get_base_queryset(self):
        if self.request.user.is_anonymous:
            return News.objects.none()
        room_ids = self.request.user.room_set.values_list("id", flat=True)
        return News.objects.filter(room_id__in=room_ids)

    def get_feed_queryset(self):
        return self.get_base_queryset().exclude(highlighted=True).order_by("-id")


class NewsListView(NewsForUserMixin, LoginRequiredMixin, generic.TemplateView):
    template_name = "news/list.html"

    @cached_property
    def _first_batch(self) -> list[News]:
        return list(self.get_feed_queryset()[:NEWS_FEED_PAGE_SIZE])

    @context
    @property
    def news(self) -> list[News]:
        return self._first_batch

    @context
    @property
    def news_next_cursor(self) -> int | None:
        batch = self._first_batch
        return batch[-1].id if len(batch) == NEWS_FEED_PAGE_SIZE else None

    @context
    @property
    def news_initial_render(self) -> bool:
        return True

    @context
    @cached_property
    def highlighted_news(self) -> News | None:
        return self.get_base_queryset().filter(highlighted=True).first()


class NewsFeedChunkView(NewsForUserMixin, LoginRequiredMixin, generic.TemplateView):
    template_name = "shared_partials/news_batch.html"

    def get_paginate_by(self):
        try:
            limit = int(self.request.GET.get("limit", NEWS_FEED_PAGE_SIZE))
        except (TypeError, ValueError):
            return NEWS_FEED_PAGE_SIZE
        return max(1, min(limit, 50))

    def get_queryset(self):
        return self.get_feed_queryset()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
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
        context_data.update(
            {
                "news": news_batch,
                "news_next_cursor": next_cursor,
                "news_initial_render": False,
            }
        )
        return context_data
