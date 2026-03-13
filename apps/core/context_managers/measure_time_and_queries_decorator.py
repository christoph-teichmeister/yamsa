from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from apps.core.context_managers.measure_time_and_queries_context_manager import MeasureTimeAndQueriesContextManager

P = ParamSpec("P")
R = TypeVar("R")


def measure_time_and_queries_decorator(func: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Wrap a callable so it reports timing queries via the context manager."""

    @wraps(func)
    def wrapper_func(*args: P.args, **kwargs: P.kwargs) -> R:
        with MeasureTimeAndQueriesContextManager(func.__name__):
            return func(*args, **kwargs)

    return wrapper_func
