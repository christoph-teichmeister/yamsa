from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        super().ready()

        # Run auto-registry
        from apps.core.event_loop.registry import message_registry

        message_registry.autodiscover()
