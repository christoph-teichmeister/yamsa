from django.views import generic
from django_context_decorator import context

from apps.news.models import News


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def _get_news_base_qs(self):
        if self.request.user.is_authenticated:
            return News.objects.filter(
                room_id__in=self.request.user.room_set.values_list("id", flat=True)
            ).prefetch_related("comments")

        return News.objects.none()

    @context
    @property
    def news(self):
        return self._get_news_base_qs().exclude(highlighted=True)

    @context
    @property
    def highlighted_news(self):
        ret = self._get_news_base_qs().filter(highlighted=True).first()
        return ret
