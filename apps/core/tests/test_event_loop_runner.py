"""Tests that ensure the event-loop runner emits logging events on failures."""

import logging
from dataclasses import dataclass

import pytest
from django.test import TestCase

from apps.core.event_loop.messages import Command, Event
from apps.core.event_loop.registry import message_registry
from apps.core.event_loop.runner import handle_command, handle_event, logger


@dataclass
class _DummyContext:
    """Empty context for dummy messages."""


class _DummyCommand(Command):
    Context = _DummyContext


class _DummyEvent(Event):
    Context = _DummyContext


def _failing_command_handler(context: _DummyContext) -> None:
    msg = "command handler boom"
    raise RuntimeError(msg)


def _failing_event_handler(context: _DummyContext) -> None:
    msg = "event handler boom"
    raise RuntimeError(msg)


class _CaptureHandler(logging.Handler):
    """Collect emitted log records for later inspection."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class RunnerLoggingTests(TestCase):
    """Ensure the runner logs context while re-raising handler exceptions."""

    def setUp(self):
        self.capture_handler = _CaptureHandler()
        logger.addHandler(self.capture_handler)
        self._original_level = logger.level
        logger.setLevel(logging.DEBUG)

    def tearDown(self):
        logger.removeHandler(self.capture_handler)
        self._cleanup_registry_entry(message_registry.command_dict, _DummyCommand, _failing_command_handler)
        self._cleanup_registry_entry(message_registry.event_dict, _DummyEvent, _failing_event_handler)
        logger.setLevel(self._original_level)

    def _cleanup_registry_entry(self, mapping: dict, key: type, handler) -> None:
        handlers = mapping.get(key)
        if not handlers:
            return
        while handler in handlers:
            handlers.remove(handler)
        if not handlers:
            mapping.pop(key, None)

    def _register_command_handler(self):
        handlers = message_registry.command_dict.setdefault(_DummyCommand, [])
        handlers.append(_failing_command_handler)

    def _register_event_handler(self):
        handlers = message_registry.event_dict.setdefault(_DummyEvent, [])
        handlers.append(_failing_event_handler)

    def _latest_error_record(self, level: int) -> logging.LogRecord | None:
        for record in reversed(self.capture_handler.records):
            if record.levelno >= level:
                return record
        return None

    def test_handle_command_exception_logs_context(self):
        self._register_command_handler()
        self.capture_handler.records.clear()
        command = _DummyCommand({})

        with pytest.raises(RuntimeError):
            handle_command(command, [])

        record = self._latest_error_record(logging.ERROR)
        assert record is not None, "Expected an ERROR record when the handler raises"
        assert "Exception handling command" in record.getMessage()
        assert command.__class__.__name__ in record.getMessage()
        assert command.uuid in record.getMessage()
        assert record.exc_info is not None

    def test_handle_event_exception_logs_context(self):
        self._register_event_handler()
        self.capture_handler.records.clear()
        event = _DummyEvent({})

        with pytest.raises(RuntimeError):
            handle_event(event, [])

        record = self._latest_error_record(logging.ERROR)
        assert record is not None, "Expected an ERROR record when the handler raises"
        assert "Exception handling event" in record.getMessage()
        assert event.__class__.__name__ in record.getMessage()
        assert event.uuid in record.getMessage()
        assert record.exc_info is not None
