import logging

from django.db import transaction

from apps.core.event_loop.messages import Command, Event, Message
from apps.core.event_loop.registry import message_registry

logger = logging.getLogger(__name__)


def handle_message(message_list: Message | list[Message]):
    queue = message_list if isinstance(message_list, list) else [message_list]

    # TODO CT: I moved this to core.apps - idk if this is necessary here
    # # Run auto-registry
    # from apps.core.domain import message_registry
    #
    # message_registry.autodiscover()

    while queue:
        message = queue.pop(0)

        if isinstance(message, Event):
            handle_event(message, queue)
            continue

        elif isinstance(message, Command):
            handle_command(message, queue)
            continue

        msg = f"{message} was not an Event or Command"
        raise Exception(msg)


def handle_command(command: Command, queue: list[Message]):
    handler_list = message_registry.command_dict.get(command.__class__, [])
    for handler in handler_list:
        try:
            # TODO CT: Warum ist der rückgabewert hier wichtig?
            logger.info(
                "Handling command '%s' (%s) with handler '%s'",
                command.__class__.__name__,
                command.uuid,
                handler.__name__,
            )
            # TODO CT: das sollte um das ganze handle_message
            with transaction.atomic():
                new_messages = handler(command.Context) or []
                new_messages = new_messages if isinstance(new_messages, list) else [new_messages]
                uuid_list = [f"{m!s}" for m in new_messages]
                logger.debug("New messages: %s", uuid_list)
                queue.extend(new_messages)
        except Exception:
            logger.exception(
                "Exception handling command %s (%s) with handler '%s'",
                command.__class__.__name__,
                command.uuid,
                handler.__name__,
            )
            raise


def handle_event(event: Event, queue: list[Message]):
    handler_list = message_registry.event_dict.get(event.__class__, [])
    for handler in handler_list:
        try:
            logger.info(
                "Handling event '%s' (%s) with handler '%s'",
                event.__class__.__name__,
                event.uuid,
                handler.__name__,
            )
            with transaction.atomic():
                new_messages = handler(event.Context) or []
                new_messages = new_messages if isinstance(new_messages, list) else [new_messages]
                uuid_list = [f"{m!s}" for m in new_messages]
                logger.debug("New messages: %s", uuid_list)
                queue.extend(new_messages)
        except Exception:
            logger.exception(
                "Exception handling event %s (%s) with handler '%s'",
                event.__class__.__name__,
                event.uuid,
                handler.__name__,
            )
            raise
