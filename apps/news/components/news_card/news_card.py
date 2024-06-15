from django_components import component


@component.register("news_card")
class NewsCard(component.Component):
    template_name = "news_card/template.html"

    def get_context_data(self):
        return {}

    class Media:
        css = "news_card/style.css"
        js = "news_card/script.js"
