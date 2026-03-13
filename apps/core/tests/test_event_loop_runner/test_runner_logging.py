"""Tests that ensure the event-loop runner emits logging events on failures."""

import logging

import pytest

from apps.core.event_loop.registry import message_registry
from apps.core.event_loop.runner import handle_command, handle_event, logger

from .capture_handler import _CaptureHandler
from .dummy_command import _DummyCommand
from .dummy_context import _DummyContext
from .dummy_event import _DummyEvent


def _failing_command_handler(context: _DummyContext) -> None:
    msg = "command handler boom"
    raise RuntimeError(msg)


def _failing_event_handler(context: _DummyContext) -> None:
    msg = "event handler boom"
    raise RuntimeError(msg)


def _cleanup_registry_entry(mapping: dict, key: type, handler) -> None:
    handlers = mapping.get(key)
    if not handlers:
        return
    while handler in handlers:
        handlers.remove(handler)
    if not handlers:
        mapping.pop(key, None)


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
    _cleanup_registry_entry(message_registry.command_dict, _DummyCommand, _failing_command_handler)
    _cleanup_registry_entry(message_registry.event_dict, _DummyEvent, _failing_event_handler)


class TestRunnerLogging:
    """Ensure the runner logs context while re-raising handler exceptions."""

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
