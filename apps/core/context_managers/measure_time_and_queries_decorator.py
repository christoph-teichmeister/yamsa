from collections.abc import Callable
from functools import wraps

from apps.core.context_managers import MeasureTimeAndQueriesContextManager, P, R


def measure_time_and_queries_decorator(func: Callable[P, R]) -> Callable[P, R]:
    """Wrap a callable so it reports timing queries via the context manager."""

    @wraps(func)
    def wrapper_func(*args: P.args, **kwargs: P.kwargs) -> R:
        with MeasureTimeAndQueriesContextManager(func.__name__):
            return func(*args, **kwargs)

    return wrapper_func
