import time
from collections.abc import Callable
from contextlib import AbstractContextManager, ContextDecorator
from typing import Any

from django.conf import settings
from django.db import connection


class _QueryExecutionCounter:
    def __init__(self) -> None:
        self.count = 0

    def __call__(
        self,
        execute: Callable[..., Any],
        sql: Any,
        params: Any,
        many: bool,
        context: Any,
    ) -> Any:
        self.count += 1
        return execute(sql, params, many, context)


class MeasureTimeAndQueriesContextManager(ContextDecorator):
    def __init__(self, function_name: str, *, print_when_debug: bool | None = None) -> None:
        self.function_name = function_name
        self._print_when_debug = settings.DEBUG if print_when_debug is None else print_when_debug
        self.last_query_count: int | None = None
        self.last_duration: float | None = None
        self._query_counter: _QueryExecutionCounter | None = None
        self._wrapper_cm: AbstractContextManager[Any] | None = None
        self._queries_before: int = 0
        self._start_time: float = 0.0

        super().__init__()

    def __enter__(self):
        execute_wrapper = getattr(connection, "execute_wrapper", None)

        if execute_wrapper:
            self._query_counter = _QueryExecutionCounter()
            self._wrapper_cm = execute_wrapper(self._query_counter)
            self._wrapper_cm.__enter__()
        else:
            self._queries_before = len(connection.queries)

        self._start_time = time.time()
        self.last_query_count = None
        self.last_duration = None
        return self

    def __exit__(self, *exc):
        end = time.time()
        if self._wrapper_cm:
            self._wrapper_cm.__exit__(*exc)

        if self._query_counter:
            self.last_query_count = self._query_counter.count
        else:
            queries_after = len(connection.queries)
            self.last_query_count = queries_after - self._queries_before

        self.last_duration = end - self._start_time

        if self._print_when_debug:
            print(f"{self.function_name} took {self.last_duration} seconds and made {self.last_query_count} queries\n")

        return False


def measure_time_and_queries_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper_func(*args: Any, **kwargs: Any) -> Any:
        with MeasureTimeAndQueriesContextManager(func.__name__):
            return func(*args, **kwargs)

    return wrapper_func
