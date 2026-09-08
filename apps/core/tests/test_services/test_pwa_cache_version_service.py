from django.test import override_settings

from apps.core.services.pwa_cache_version_service import FALLBACK_VERSION, resolve_cache_version


@override_settings(SENTRY_RELEASE="feature/offline@1.2.3", RENDER_GIT_COMMIT="")
def test_release_is_sanitised_into_a_cache_name():
    assert resolve_cache_version() == "feature-offline-1-2-3"


@override_settings(SENTRY_RELEASE="", RENDER_GIT_COMMIT="")
def test_without_a_release_the_assets_stand_in_for_one(tmp_path):
    """A host that names its builds differently, or a run from a working copy."""
    stats_file = tmp_path / "webpack-stats.json"
    stats_file.write_text('{"status": "done"}', encoding="utf-8")

    with override_settings(WEBPACK_LOADER={"DEFAULT": {"STATS_FILE": str(stats_file)}}, STATIC_ROOT=""):
        first = resolve_cache_version()
        assert first.startswith("assets-")

        stats_file.write_text('{"status": "done", "changed": true}', encoding="utf-8")
        assert resolve_cache_version() != first


@override_settings(SENTRY_RELEASE="", RENDER_GIT_COMMIT="", STATIC_ROOT="")
def test_without_any_asset_input_the_version_stays_constant():
    with override_settings(WEBPACK_LOADER={"DEFAULT": {}}):
        assert resolve_cache_version() == FALLBACK_VERSION


@override_settings(SENTRY_RELEASE="", RENDER_GIT_COMMIT="abc123def456")
def test_render_names_the_build_when_nothing_else_does():
    """The variable that actually exists in production - Render sets it, nobody has to."""
    assert resolve_cache_version() == "abc123def456"


@override_settings(SENTRY_RELEASE="explicitly-configured", RENDER_GIT_COMMIT="abc123def456")
def test_a_configured_release_wins_over_the_commit():
    assert resolve_cache_version() == "explicitly-configured"
