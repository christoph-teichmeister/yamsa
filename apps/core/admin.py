from ai_django_core.admin.model_admins.mixins import CommonInfoAdminMixin


class YamsaCommonInfoAdminMixin(CommonInfoAdminMixin):
    extra_fields_for_fieldset: tuple = ()

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        fieldsets += (
            (
                "Sonstige Informationen",
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
