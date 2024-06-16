from typing import Any

from django.urls import reverse
from django_components import component


@component.register("NewsList")
class NewsList(component.Component):
    template_name = "news_list/template.html"

    def get_context_data(self) -> dict[str, Any]:
        return {"view_url": reverse("news:htmx-list")}
