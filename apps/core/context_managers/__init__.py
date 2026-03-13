from typing import ParamSpec, TypeVar

from apps.core.context_managers._query_execution_counter import _QueryExecutionCounter
from apps.core.context_managers.measure_time_and_queries_context_manager import MeasureTimeAndQueriesContextManager
from apps.core.context_managers.measure_time_and_queries_decorator import measure_time_and_queries_decorator

P = ParamSpec("P")
R = TypeVar("R")
