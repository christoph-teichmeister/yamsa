"""
Tests for ListLoader component (Issue #144)

Tests the skeleton screen → overlay switching mechanism with 800ms threshold.
"""
from django.template import Context, Template


class TestListLoaderComponent:
    """Test the _list_loader.html template component."""

    def test_skeleton_renders(self):
        """Skeleton screen should render with configurable item count."""
        template = Template(
            '{% load %}{% include "shared_partials/_list_loader.html" with loader_id="test-loader" skeleton_count=3 %}'
        )
        output = template.render(Context({}))

        # Should contain skeleton items
        assert 'skeleton-item' in output
        assert 'test-loader-skeleton' in output

    def test_overlay_renders(self):
        """Overlay should render with localized message."""
        template = Template(
            '{% load %}{% include "shared_partials/_list_loader.html" with loader_id="test-loader" skeleton_count=5 %}'
        )
        output = template.render(Context({}))

        # Should contain overlay
        assert 'test-loader-overlay' in output
        assert 'loading-overlay-message' in output

    def test_javascript_event_handlers(self):
        """JavaScript should set up HTMX event listeners."""
        template = Template(
            '{% load %}{% include "shared_partials/_list_loader.html" with loader_id="test-loader" skeleton_count=5 %}'
        )
        output = template.render(Context({}))

        # Should contain HTMX event handler setup
        assert 'htmx:beforeRequest' in output
        assert 'htmx:afterSwap' in output
        assert '800' in output  # 800ms threshold
