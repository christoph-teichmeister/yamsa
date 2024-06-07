from apps.core.event_loop.registry import message_registry
from apps.core.event_loop.runner import handle_message


class EmitModelEventOnSaveMixin:
    class ModelEvents:
        class Created:
            label = "Created"
            attr_name = "_model_created_event_klass"

        class Changed:
            label = "Changed"
            attr_name = "_model_changed_event_klass"

        class Deleted:
            label = "Deleted"
            attr_name = "_model_deleted_event_klass"

        def get_model_events_as_tuple(self) -> tuple:
            return self.Created, self.Changed, self.Deleted

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for model_event in self.ModelEvents().get_model_events_as_tuple():
            event_handler_class_list = list(
                filter(
                    lambda klass: f"{self._meta.object_name}{model_event.label}" in str(klass),
                    message_registry.event_dict,
                )
            )

            event_handler_class = None
            if len(event_handler_class_list) > 0:
                event_handler_class = event_handler_class_list[0]

            setattr(self, model_event.attr_name, event_handler_class)

    def expand_model_event_context(self) -> dict:
        return {}

    def save(self, *args, **kwargs):
        model_event_type = self.ModelEvents.Created if not self.id else self.ModelEvents.Changed

        super().save(*args, **kwargs)

        self._send_message(
            model_event_class=getattr(self, model_event_type.attr_name), context_label=model_event_type.label
        )

    def delete(self, using=None, keep_parents=False):
        del_operation = super().delete(using, keep_parents)

        self._send_message(
            model_event_class=getattr(self, self.ModelEvents.Deleted.attr_name),
            context_label=self.ModelEvents.Deleted.label,
        )

        return del_operation

    def _send_message(self, model_event_class, context_label: str):
        if model_event_class is None:
            return

        handle_message(
            model_event_class(
                context_data={
                    "instance": self,
                    **self.expand_model_event_context().get(context_label.lower(), {}),
                }
            )
        )
