import io
from contextlib import redirect_stdout

import pytest
from pytest_django.fixtures import Settings

from apps.account.models import User
from apps.core.context_managers import MeasureTimeAndQueriesContextManager


@pytest.mark.django_db
class TestMeasureTimeAndQueriesContextManager:
    def test_prints_measurement_when_debug_true(self, settings: Settings):
        settings.DEBUG = True
        buffer = io.StringIO()

        with redirect_stdout(buffer), MeasureTimeAndQueriesContextManager("context-manager") as manager:
            User.objects.count()

        output = buffer.getvalue()

        assert manager.last_query_count is not None
        assert manager.last_query_count >= 1
        assert "context-manager took" in output
        assert "and made" in output

    def test_suppresses_output_when_debug_false(self, settings: Settings):
        settings.DEBUG = False
        buffer = io.StringIO()

        with redirect_stdout(buffer), MeasureTimeAndQueriesContextManager("silent") as manager:
            User.objects.count()

        assert buffer.getvalue() == ""
        assert manager.last_query_count is not None
