from apps.core.event_loop.messages import Event
from apps.core.tests.test_event_loop_runner.dummy_context import _DummyContext


class _DummyEvent(Event):
    Context = _DummyContext
