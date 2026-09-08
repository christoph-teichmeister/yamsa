from django.test import override_settings

from apps.core.services.pwa_cache_version_service import FALLBACK_VERSION, resolve_cache_version


@override_settings(RELEASE="feature/offline@1.2.3")
def test_the_release_is_sanitised_into_a_cache_name():
    assert resolve_cache_version() == "feature-offline-1-2-3"


@override_settings(RELEASE="")
def test_without_a_release_the_assets_stand_in_for_one(tmp_path):
    """A run from a working copy, or a host that does not name its builds."""
    stats_file = tmp_path / "webpack-stats.json"
    stats_file.write_text('{"status": "done"}', encoding="utf-8")

    with override_settings(WEBPACK_LOADER={"DEFAULT": {"STATS_FILE": str(stats_file)}}, STATIC_ROOT=""):
        first = resolve_cache_version()
        assert first.startswith("assets-")

        stats_file.write_text('{"status": "done", "changed": true}', encoding="utf-8")
        assert resolve_cache_version() != first


@override_settings(RELEASE="", STATIC_ROOT="")
def test_without_any_asset_input_the_version_stays_constant():
    with override_settings(WEBPACK_LOADER={"DEFAULT": {}}):
        assert resolve_cache_version() == FALLBACK_VERSION
