import logging

from django.db import transaction

from apps.core.event_loop.messages import Command, Event, Message
from apps.core.event_loop.registry import message_registry

logger = logging.getLogger(__name__)


def handle_message(message_list: Message | list[Message]) -> None:
    """Process commands/events once Django has populated the registry on startup."""
    # The message registry is populated when `apps.core.apps.CoreConfig.ready()` runs,
    # so the runner never has to import or autodiscover handlers itself.
    queue = message_list if isinstance(message_list, list) else [message_list]

    while queue:
        message = queue.pop(0)

        if isinstance(message, Event):
            handle_event(message, queue)
            continue

        if isinstance(message, Command):
            handle_command(message, queue)
            continue

        msg = f"{message} was not an Event or Command"
        raise TypeError(msg)


def handle_command(command: Command, queue: list[Message]) -> None:
    _dispatch(message_registry.command_dict, "command", command, command.Context, queue)


def handle_event(event: Event, queue: list[Message]) -> None:
    _dispatch(message_registry.event_dict, "event", event, event.Context, queue)


def _dispatch(registry: dict, kind: str, message: Message, context: object, queue: list[Message]) -> None:
    """Run every handler of the message, then re-raise the first failure.

    A failing handler must not keep later handlers of the same message from running (e.g. a failed push must not
    skip debt recalculation), so failures are collected instead of aborting the loop.
    """
    first_error: Exception | None = None
    for handler in registry.get(message.__class__, []):
        logger.info(
            "Handling %s '%s' (%s) with handler '%s'", kind, message.__class__.__name__, message.uuid, handler.__name__
        )
        try:
            if getattr(handler, "atomic", True):
                with transaction.atomic():
                    new_messages = handler(context) or []
            else:
                new_messages = handler(context) or []
        except Exception as error:
            logger.exception(
                "Exception handling %s %s (%s) with handler '%s'",
                kind,
                message.__class__.__name__,
                message.uuid,
                handler.__name__,
            )
            first_error = first_error or error
            continue

        new_messages = new_messages if isinstance(new_messages, list) else [new_messages]
        logger.debug("New messages: %s", [f"{m!s}" for m in new_messages])
        queue.extend(new_messages)

    if first_error:
        raise first_error
