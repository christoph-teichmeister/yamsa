import io
from contextlib import redirect_stdout

import pytest

from apps.account.models import User
from apps.core.context_managers import (
    MeasureTimeAndQueriesContextManager,
    measure_time_and_queries_decorator,
)


@pytest.mark.django_db
class TestMeasureTimeAndQueriesContextManager:
    def test_prints_measurement_when_debug_true(self, settings):
        settings.DEBUG = True
        buffer = io.StringIO()

        with redirect_stdout(buffer), MeasureTimeAndQueriesContextManager("context-manager") as manager:
            User.objects.count()

        output = buffer.getvalue()

        assert manager.last_query_count and manager.last_query_count >= 1
        assert "context-manager took" in output
        assert "and made" in output

    def test_suppresses_output_when_debug_false(self, settings):
        settings.DEBUG = False
        buffer = io.StringIO()

        with redirect_stdout(buffer), MeasureTimeAndQueriesContextManager("silent") as manager:
            User.objects.count()

        assert buffer.getvalue() == ""
        assert manager.last_query_count is not None


@pytest.mark.django_db
class TestMeasureTimeAndQueriesDecorator:
    def test_decorator_exposes_result_and_prints_when_debug_true(self, settings):
        settings.DEBUG = True
        buffer = io.StringIO()
        expected_count = User.objects.count()

        @measure_time_and_queries_decorator
        def count_users():
            return User.objects.count()

        with redirect_stdout(buffer):
            result = count_users()

        assert result == expected_count
        output = buffer.getvalue()
        assert "count_users took" in output
        assert "and made" in output
