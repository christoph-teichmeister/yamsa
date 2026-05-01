import pytest

from apps.config.storage import ManifestStaticFilesStorage


class TestManifestStaticFilesStoredName:
    def _make_storage(self):
        return ManifestStaticFilesStorage.__new__(ManifestStaticFilesStorage)

    def test_missing_bootstrap_toggle_map_returns_name(self, monkeypatch):
        storage = self._make_storage()
        base = ManifestStaticFilesStorage.__bases__[0]
        monkeypatch.setattr(
            base, "_stored_name", lambda self, name, hashed_files: (_ for _ in ()).throw(ValueError("missing"))
        )

        result = storage._stored_name("passkeys/js/bootstrap-toggle.min.js.map", {})

        assert result == "passkeys/js/bootstrap-toggle.min.js.map"

    def test_missing_non_map_asset_raises(self, monkeypatch):
        storage = self._make_storage()
        base = ManifestStaticFilesStorage.__bases__[0]
        monkeypatch.setattr(
            base, "_stored_name", lambda self, name, hashed_files: (_ for _ in ()).throw(ValueError("missing"))
        )

        with pytest.raises(ValueError):
            storage._stored_name("some/missing/asset.js", {})
