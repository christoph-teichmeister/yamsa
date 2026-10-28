import contextlib
import importlib
from collections.abc import Callable

from django.conf import settings

from apps.core.event_loop.messages import Command, Event


class MessageRegistry:
    """Singleton for registering messages classes in."""

    def __init__(self) -> None:
        self.command_dict: dict = {}
        self.event_dict: dict = {}

    def register_command(self, command: Command, *, atomic: bool = True) -> Callable:
        def decorator(decoratee: Callable) -> Callable:
            # Ensure that registered message is of correct type
            if not (issubclass(command, Command)):
                msg = (
                    f'Trying to register message function of wrong type: "{command.__name__}" '
                    f'on handler "{decoratee.__name__}".'
                )
                raise TypeError(msg)

            # The runner reads this flag: handlers doing slow I/O (push, mail) must not hold a DB transaction open.
            decoratee.atomic = atomic

            # Add decoratee to dependency list
            if command not in self.command_dict:
                self.command_dict[command] = [decoratee]
            else:
                self.command_dict[command].append(decoratee)

            # Return decoratee
            return decoratee

        return decorator

    def register_event(self, event: Event, *, atomic: bool = True) -> Callable:
        def decorator(decoratee: Callable) -> Callable:
            # Ensure that registered message is of correct type
            if not (issubclass(event, Event)):
                msg = (
                    f'Trying to register message function of wrong type: "{event.__name__}" '
                    f'on handler "{decoratee.__name__}".'
                )
                raise TypeError(msg)

            # The runner reads this flag: handlers doing slow I/O (push, mail) must not hold a DB transaction open.
            decoratee.atomic = atomic

            # Add decoratee to dependency list
            if event not in self.event_dict:
                self.event_dict[event] = [decoratee]
            else:
                self.event_dict[event].append(decoratee)

            # Return decoratee
            return decoratee

        return decorator

    def autodiscover(self) -> None:
        """Detects message registries which have been registered via the "register_*" decorator."""
        if len(self.command_dict) + len(self.event_dict) > 0:
            return

        for app in settings.INSTALLED_APPS:
            if app.startswith("apps."):
                self._import_handler_modules(app)

        self._log_detected("commands", self.command_dict)
        self._log_detected("events", self.event_dict)
        print(f"\n### {len(self.command_dict) + len(self.event_dict)} message functions detected. ###\n")

    @staticmethod
    def _import_handler_modules(app: str) -> None:
        """Import the app's handler modules so their "register_*" decorators run."""
        for message_type in ("commands", "events"):
            handler_dir = settings.APPS_DIR / app.removeprefix("apps.") / "handlers" / message_type
            if not handler_dir.is_dir():
                continue
            for module in handler_dir.iterdir():
                if module.suffix == ".py":
                    with contextlib.suppress(ModuleNotFoundError):
                        importlib.import_module(f"{app}.handlers.{message_type}.{module.stem}")

    @staticmethod
    def _log_detected(message_type: str, message_dict: dict) -> None:
        print(f"\nMessage autodiscovery running for {message_type}...")
        for message, handlers in message_dict.items():
            handler_list = ", ".join(handler.__name__ for handler in handlers)
            print(f"* {message.__name__}: [{handler_list}]")


message_registry = MessageRegistry()
