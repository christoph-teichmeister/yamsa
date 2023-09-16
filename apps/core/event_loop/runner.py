from django.db import transaction

from apps.core.event_loop.messages import Command, Event, Message
from apps.core.event_loop.registry import message_registry


def handle_message(message_list: Message | list[Message]):
    if isinstance(message_list, list):
        queue = message_list
    else:
        queue = [message_list]

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

        raise Exception(f"{message} was not an Event or Command")


def handle_command(command: Command, queue: list[Message]):
    handler_list = message_registry.command_dict.get(command.__class__, list())
    for handler in handler_list:
        try:
            # todo warum ist der rückgabewert hier wichtig?
            # todo logger bauen, den man über das django logging in den settings konfigurieren kann
            #  context, request-datum, user etc.
            print(
                f"\n Handling command '{command.__class__.__name__}' ({command.uuid}) with handler '{handler.__name__}'"
            )
            # todo das sollte um das ganze handle_message
            with transaction.atomic():
                new_messages = handler(command.Context) or []
                new_messages = new_messages if isinstance(new_messages, list) else [new_messages]
                uuid_list = [f"{str(m)}" for m in new_messages]
                print(f"New messages: {str(uuid_list)}")
                queue.extend(new_messages)
        except Exception as e:
            print(f"Exception handling command {command.__class__.__name__}: {str(e)}")
            raise e


def handle_event(event: Event, queue: list[Message]):
    handler_list = message_registry.event_dict.get(event.__class__, list())
    for handler in handler_list:
        try:
            print(f"\nHandling event '{event.__class__.__name__}' ({event.uuid}) with handler '{handler.__name__}'")
            with transaction.atomic():
                new_messages = handler(event.Context) or []
                new_messages = new_messages if isinstance(new_messages, list) else [new_messages]
                uuid_list = [f"{str(m)}" for m in new_messages]
                print(f"New messages: {str(uuid_list)}")
                queue.extend(new_messages)
        except Exception as e:
            print(f"Exception handling event {event.__class__.__name__}: {str(e)}")
            raise e
