from typing import Any

from django_components import component

from apps.news.models import News


@component.register("NewsCard")
class NewsCard(component.Component):
    template_name = "news_card/template.html"

    def get_context_data(self, news: News, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {**super().get_context_data(*args, **kwargs), "news": news}
