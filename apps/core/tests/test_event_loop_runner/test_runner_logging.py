"""Tests that ensure the event-loop runner emits logging events on failures."""

import logging

import pytest

from apps.core.event_loop.registry import message_registry
from apps.core.event_loop.runner import handle_command, handle_event, handle_message, logger
from apps.core.tests.helpers.capture_handler import _CaptureHandler
from apps.core.tests.helpers.dummy_command import _DummyCommand
from apps.core.tests.helpers.dummy_context import _DummyContext
from apps.core.tests.helpers.dummy_event import _DummyEvent


def _failing_command_handler(context: _DummyContext) -> None:
    msg = "command handler boom"
    raise RuntimeError(msg)


def _failing_event_handler(context: _DummyContext) -> None:
    msg = "event handler boom"
    raise RuntimeError(msg)


def _latest_error_record(handler: _CaptureHandler, level: int) -> logging.LogRecord | None:
    for record in reversed(handler.records):
        if record.levelno >= level:
            return record
    return None


@pytest.fixture
def capture_handler():
    handler = _CaptureHandler()
    logger.addHandler(handler)
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)


@pytest.fixture(autouse=True)
def cleanup_registry():
    yield
    message_registry.command_dict.pop(_DummyCommand, None)
    message_registry.event_dict.pop(_DummyEvent, None)


class TestEventLoopRunner:
    """Ensure the runner logs context while re-raising handler exceptions and keeps dispatching."""

    def _register_command_handler(self):
        handlers = message_registry.command_dict.setdefault(_DummyCommand, [])
        handlers.append(_failing_command_handler)

    def _register_event_handler(self):
        handlers = message_registry.event_dict.setdefault(_DummyEvent, [])
        handlers.append(_failing_event_handler)

    def test_handle_command_exception_logs_context(self, capture_handler):
        self._register_command_handler()
        capture_handler.records.clear()
        command = _DummyCommand({})

        with pytest.raises(RuntimeError):
            handle_command(command, [])

        record = _latest_error_record(capture_handler, logging.ERROR)
        assert record is not None, "Expected an ERROR record when the handler raises"
        assert "Exception handling command" in record.getMessage()
        assert command.__class__.__name__ in record.getMessage()
        assert command.uuid in record.getMessage()
        assert record.exc_info is not None

    def test_handle_event_exception_logs_context(self, capture_handler):
        self._register_event_handler()
        capture_handler.records.clear()
        event = _DummyEvent({})

        with pytest.raises(RuntimeError):
            handle_event(event, [])

        record = _latest_error_record(capture_handler, logging.ERROR)
        assert record is not None, "Expected an ERROR record when the handler raises"
        assert "Exception handling event" in record.getMessage()
        assert event.__class__.__name__ in record.getMessage()
        assert event.uuid in record.getMessage()
        assert record.exc_info is not None

    @pytest.mark.django_db
    def test_handle_message_dispatches_command_and_event_handlers(self):
        processed: list[str] = []

        @message_registry.register_command(command=_DummyCommand)
        def _recording_command_handler(context: _DummyContext) -> _DummyEvent:
            processed.append("command")
            return _DummyEvent(context)

        @message_registry.register_event(event=_DummyEvent)
        def _recording_event_handler(_context: _DummyContext) -> None:
            processed.append("event")

        handle_message(_DummyCommand({}))

        assert processed == ["command", "event"]
