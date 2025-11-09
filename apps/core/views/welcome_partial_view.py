from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.news.constants import NEWS_FEED_PAGE_SIZE
from apps.news.models import News


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect(redirect_to=reverse(viewname="account:login"))
        return super().get(request, *args, **kwargs)

    def _get_news_base_qs(self):
        if self.request.user.is_authenticated:
            return News.objects.filter(room_id__in=self.request.user.room_set.values_list("id", flat=True))

        return News.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = self._get_news_base_qs()
        news_queryset = base_queryset.exclude(highlighted=True).order_by("-id")
        news_batch = list(news_queryset[:NEWS_FEED_PAGE_SIZE])
        next_cursor = news_batch[-1].id if len(news_batch) == NEWS_FEED_PAGE_SIZE else None

        context.update(
            {
                "news": news_batch,
                "news_next_cursor": next_cursor,
                "news_initial_render": True,
                "highlighted_news": base_queryset.filter(highlighted=True).first(),
            }
        )
        return context
