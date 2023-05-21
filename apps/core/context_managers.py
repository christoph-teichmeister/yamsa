import time
from contextlib import ContextDecorator

from django.db import connection


class measure_time_and_queries(ContextDecorator):
    def __init__(self, function_name: str) -> None:
        self.function_name = function_name

        super().__init__()

    def __enter__(
        self,
    ):
        self.queries_before_qs = len(connection.queries)
        self.start = time.time()
        return self

    def __exit__(self, *exc):
        queries_after_qs = len(connection.queries)
        end = time.time()

        print(
            f"{self.function_name} took {end - self.start} seconds and made {queries_after_qs - self.queries_before_qs} queries\n"
        )

        return False
