from dataclasses import dataclass, field
from typing import Any

from django_components import component


@dataclass
class TableConfig:
    keys: list[str] = field(default_factory=lambda: ["id"])


@component.register("PaginatedLazyTable")
class PaginatedLazyTable(component.Component):
    template_name = "paginated_lazy_table/template.html"

    def get_context_data(
        self, view_url: str, object_list: list[dict], table_config: TableConfig = None
    ) -> dict[str, Any]:
        if table_config is None or table_config == "":
            table_config = TableConfig()

        return {"view_url": view_url, "object_list": object_list, "table_config": table_config}
