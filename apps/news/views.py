from django.urls import reverse
from django.views import generic

from apps.core.components.paginated_lazy_table.paginated_lazy_table import TableConfig
from apps.news.models import News


class OpenedNewsHTMXView(generic.DetailView):
    queryset = News.objects.all()
    template_name = "shared_partials/news_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opened"] = True
        return context


class NewsListHTMXView(generic.ListView):
    paginate_by = 20
    template_name = "htmx/news_list.html"

    def get_queryset(self):
        return News.objects.visible_for(user=self.request.user).select_related("room")

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=object_list, **kwargs)
        ctx["table_config"] = TableConfig(keys=["title", "created_at", "room.name"])
        ctx["view_url"] = reverse("news:htmx-list")
        return ctx
