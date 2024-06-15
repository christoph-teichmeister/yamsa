from django_components import component

from apps.news.models import News


@component.register("news_card")
class NewsCard(component.Component):
    template_name = "news_card/template.html"

    def get_context_data(self, news: News):
        return {"news": news}

    class Media:
        css = "news_card/style.css"
        js = "news_card/script.js"
