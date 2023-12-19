import importlib
import os

from django.conf import settings

from apps.core.event_loop.messages import Command, Event


class MessageRegistry:
    """
    Singleton for registering messages classes in.
    """

    def __init__(self):
        self.command_dict: dict = {}
        self.event_dict: dict = {}

    def register_command(self, command: Command):
        def decorator(decoratee):
            # Ensure that registered message is of correct type
            if not (issubclass(command, Command)):
                raise TypeError(
                    f'Trying to register message function of wrong type: "{command.__name__}" '
                    f'on handler "{decoratee.__name__}".'
                )

            # Add decoratee to dependency list
            if command not in self.command_dict:
                self.command_dict[command] = [decoratee]
            else:
                self.command_dict[command].append(decoratee)

            # Return decoratee
            return decoratee

        return decorator

    def register_event(self, event: Event):
        def decorator(decoratee):
            # Ensure that registered message is of correct type
            if not (issubclass(event, Event)):
                raise TypeError(
                    f'Trying to register message function of wrong type: "{event.__name__}" '
                    f'on handler "{decoratee.__name__}".'
                )

            # Add decoratee to dependency list
            if event not in self.event_dict:
                self.event_dict[event] = [decoratee]
            else:
                self.event_dict[event].append(decoratee)

            # Return decoratee
            return decoratee

        return decorator

    def autodiscover(self):
        """
        Detects message registries which have been registered via the "register_*" decorator.
        """
        if len(self.command_dict) + len(self.event_dict) > 0:
            return

        # Import all notification.pys in all installed apps to trigger notification class registration via decorator
        for app in settings.INSTALLED_APPS:
            if not app[:5] == "apps.":
                continue
            custom_package = app.replace("apps.", "")
            for message_type in ["commands", "events"]:
                try:
                    for module in os.listdir(settings.APPS_DIR / custom_package / "handlers" / message_type):
                        if module[-3:] == ".py":
                            module_name = module.replace(".py", "")
                            try:
                                importlib.import_module(f"{app}.handlers.{message_type}.{module_name}")
                            except ModuleNotFoundError:
                                pass
                except FileNotFoundError:
                    pass

        # Log to shell which functions have been detected
        print("\nMessage autodiscovery running for commands...")
        for command in self.command_dict:
            handler_list = ", ".join(x.__name__ for x in self.command_dict[command])
            print(f"* {command.__name__}: [{handler_list}]")

        print("\nMessage autodiscovery running for events...")
        for event in self.event_dict:
            handler_list = ", ".join(x.__name__ for x in self.event_dict[event])
            print(f"* {event.__name__}: [{handler_list}]")

        print(f"\n### {len(self.command_dict) + len(self.event_dict)} message functions detected. ###\n")


message_registry = MessageRegistry()
