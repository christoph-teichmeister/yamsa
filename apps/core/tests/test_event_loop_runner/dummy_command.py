from apps.core.event_loop.messages import Command
from apps.core.tests.test_event_loop_runner.dummy_context import _DummyContext


class _DummyCommand(Command):
    Context = _DummyContext
