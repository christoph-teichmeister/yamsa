from typing import Any

from django_components import component

from apps.core.components.paginated_lazy_table.paginated_lazy_table import TableConfig


@component.register("NewsList")
class NewsList(component.Component):
    template_name = "news_list/template.html"

    def get_context_data(self, view_url: str) -> dict[str, Any]:
        return {
            "table_config": TableConfig(keys=["title", "created_at", "room.name"]),
            "view_url": view_url,
        }
