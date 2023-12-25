from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.news.models import News


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect(redirect_to=reverse(viewname="account-user-login"))
        return super().get(request, *args, **kwargs)

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
        return self._get_news_base_qs().filter(highlighted=True).first()
