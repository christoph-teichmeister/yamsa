from django.contrib.auth import mixins
from django.urls import reverse
from django.views import generic

from apps.news.forms import NewsCommentCreateForm
from apps.news.models import News, NewsComment


class OpenedNewsHTMXView(generic.DetailView):
    queryset = News.objects.all()
    template_name = "shared_partials/news_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opened"] = True
        return context


class NewsCommentCreateHTMXView(mixins.LoginRequiredMixin, generic.CreateView):
    model = NewsComment
    form_class = NewsCommentCreateForm
    template_name = "shared_partials/news_card.html"

    def get_success_url(self):
        return reverse(viewname="htmx-opened-news", kwargs={"pk": self.object.news.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opened"] = True
        return context


class ClosedNewsHTMXView(generic.DetailView):
    queryset = News.objects.all()
    template_name = "shared_partials/news_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opened"] = False
        return context
