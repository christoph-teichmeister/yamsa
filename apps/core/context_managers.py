import time
import types
from collections.abc import Callable
from contextlib import AbstractContextManager, ContextDecorator
from functools import wraps
from typing import ParamSpec, Self, TypeVar

from django.conf import settings
from django.db import connection


class _QueryExecutionCounter:
    """Tracks how many SQL executions occur via Django's execute_wrapper."""

    def __init__(self) -> None:
        self.count = 0

    def __call__(
        self,
        execute: Callable[..., object],
        sql: object,
        params: object,
        many: bool,
        context: object,
    ) -> object:
        self.count += 1
        return execute(sql, params, many, context)


P = ParamSpec("P")
R = TypeVar("R")


class MeasureTimeAndQueriesContextManager(ContextDecorator):
    """Context manager that measures execution time and query count for a block."""

    def __init__(self, function_name: str, *, print_when_debug: bool | None = None) -> None:
        self.function_name = function_name
        self._print_when_debug = settings.DEBUG if print_when_debug is None else print_when_debug
        self.last_query_count: int | None = None
        self.last_duration: float | None = None
        self._query_counter: _QueryExecutionCounter | None = None
        self._wrapper_cm: AbstractContextManager[None] | None = None
        self._queries_before: int = 0
        self._start_time: float = 0.0

        super().__init__()

    def __enter__(self) -> Self:
        execute_wrapper = getattr(connection, "execute_wrapper", None)

        if execute_wrapper:
            self._query_counter = _QueryExecutionCounter()
            self._wrapper_cm = execute_wrapper(self._query_counter)
            self._wrapper_cm.__enter__()
        else:
            # Fall back to the legacy query log when execute_wrapper is unavailable.
            self._queries_before = len(connection.queries)

        self._start_time = time.time()
        self.last_query_count = None
        self.last_duration = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: types.TracebackType | None,
    ) -> bool | None:
        end = time.time()
        if self._wrapper_cm:
            self._wrapper_cm.__exit__(exc_type, exc, tb)

        if self._query_counter:
            self.last_query_count = self._query_counter.count
        else:
            queries_after = len(connection.queries)
            self.last_query_count = queries_after - self._queries_before

        self.last_duration = end - self._start_time

        if self._print_when_debug:
            print(f"{self.function_name} took {self.last_duration} seconds and made {self.last_query_count} queries\n")

        return False


def measure_time_and_queries_decorator(func: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Wrap a callable so it reports timing queries via the context manager."""

    @wraps(func)
    def wrapper_func(*args: P.args, **kwargs: P.kwargs) -> R:
        with MeasureTimeAndQueriesContextManager(func.__name__):
            return func(*args, **kwargs)

    return wrapper_func
