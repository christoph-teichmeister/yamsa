from django.urls import reverse
from django.views import generic

from apps.news.models import FeedItem


class HTMXFeedListContentListView(generic.ListView):
    paginate_by = 20
    template_name = "htmx/feed_list_content_list.html"

    def get_queryset(self):
        return FeedItem.objects.visible_for(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        ctx["view_url"] = reverse("news:htmx-list")
        return ctx
