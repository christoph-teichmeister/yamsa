from django.views import generic

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
        return News.objects.visible_for(user=self.request.user)
