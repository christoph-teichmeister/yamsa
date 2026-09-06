from functools import cached_property

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django_context_decorator import context

from apps.news.constants import NEWS_FEED_PAGE_SIZE
from apps.news.models import News
from apps.news.views.mixins import NewsForUserMixin


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
