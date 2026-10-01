from ambient_toolbox.admin.model_admins.mixins import CommonInfoAdminMixin
from django.db.models import Model
from django.http import HttpRequest


class YamsaCommonInfoAdminMixin(CommonInfoAdminMixin):
    extra_fields_for_fieldset: tuple = ()

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> tuple:
        fieldsets = super().get_fieldsets(request, obj)

        fieldsets += (
            (
                "Other Info",
                {
                    "fields": (
                        *self.extra_fields_for_fieldset,
                        ("created_by", "created_at"),
                        ("lastmodified_by", "lastmodified_at"),
                    )
                },
            ),
        )

        return fieldsets
