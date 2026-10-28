from collections.abc import Iterator

import pytest
from django.db import connection

from apps.core.event_loop.registry import message_registry
from apps.core.event_loop.runner import handle_event
from apps.core.tests.helpers.dummy_context import _DummyContext
from apps.core.tests.helpers.dummy_event import _DummyEvent


@pytest.fixture(autouse=True)
def cleanup_registry() -> Iterator[None]:
    yield
    message_registry.event_dict.pop(_DummyEvent, None)


@pytest.mark.django_db
class TestEventDispatch:
    def test_failing_handler_does_not_skip_later_handlers(self) -> None:
        processed: list[str] = []

        @message_registry.register_event(event=_DummyEvent)
        def _failing(_context: _DummyContext) -> None:
            msg = "boom"
            raise RuntimeError(msg)

        @message_registry.register_event(event=_DummyEvent)
        def _later(_context: _DummyContext) -> None:
            processed.append("later")

        with pytest.raises(RuntimeError, match="boom"):
            handle_event(_DummyEvent({}), [])

        assert processed == ["later"]

    def test_atomic_flag_controls_transaction_around_handler(self) -> None:
        savepoints_inside: dict[str, int] = {}

        @message_registry.register_event(event=_DummyEvent)
        def _atomic(_context: _DummyContext) -> None:
            savepoints_inside["atomic"] = len(connection.savepoint_ids)

        @message_registry.register_event(event=_DummyEvent, atomic=False)
        def _not_atomic(_context: _DummyContext) -> None:
            savepoints_inside["not_atomic"] = len(connection.savepoint_ids)

        handle_event(_DummyEvent({}), [])

        assert savepoints_inside["atomic"] == savepoints_inside["not_atomic"] + 1
