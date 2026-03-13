from collections.abc import Callable


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
