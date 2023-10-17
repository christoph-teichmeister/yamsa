import time
from contextlib import ContextDecorator

from django.db import connection


class measure_time_and_queries_context_manager(ContextDecorator):
    def __init__(self, function_name: str) -> None:
        self.function_name = function_name

        super().__init__()

    def __enter__(self):
        self.queries_before_qs = len(connection.queries)
        self.start = time.time()
        return self

    def __exit__(self, *exc):
        queries_after_qs = len(connection.queries)
        end = time.time()

        print(
            f"{self.function_name} took {end - self.start} seconds "
            f"and made {queries_after_qs - self.queries_before_qs} queries\n"
        )

        return False


def measure_time_and_queries_decorator(func):
    def wrapper_func(*args, **kwargs):
        # Do something before the function.
        queries_before_qs = len(connection.queries)
        start = time.time()

        func(*args, **kwargs)

        # Do something after the function.
        queries_after_qs = len(connection.queries)
        end = time.time()

        time_delta = end - start
        query_delta = queries_after_qs - queries_before_qs

        # print(connection.queries[-query_delta:])
        print(f"{func.__name__} took {time_delta} seconds and made {query_delta} queries\n")

    return wrapper_func
