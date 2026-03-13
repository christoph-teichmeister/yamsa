from collections.abc import Iterable, Mapping

from webpack_loader.loader import WebpackLoader


class NormalizedWebpackLoader(WebpackLoader):
    """Normalize stats files that expose chunk entries as dicts for compatibility."""

    def load_assets(self) -> dict[str, object]:
        assets = super().load_assets()
        chunks = assets.get("chunks")
        if not self._needs_normalization(chunks):
            return assets

        normalized_chunks, chunk_metadata = self._normalize_chunks(chunks)
        normalized_assets = dict(assets)
        normalized_assets["chunks"] = normalized_chunks
        normalized_assets["assets"] = self._merge_asset_metadata(normalized_assets.get("assets"), chunk_metadata)

        return normalized_assets

    @staticmethod
    def _needs_normalization(chunks: object) -> bool:
        if not isinstance(chunks, Mapping):
            return False
        return any(any(isinstance(chunk, Mapping) for chunk in (chunk_list or [])) for chunk_list in chunks.values())

    @staticmethod
    def _normalize_chunks(
        chunks: Mapping[str, Iterable[str | Mapping[str, object]] | None],
    ) -> tuple[dict[str, list[str]], dict[str, Mapping[str, object]]]:
        normalized = {}
        metadata: dict[str, Mapping[str, object]] = {}

        for bundle_name, chunk_list in chunks.items():
            normalized_list: list[str] = []
            for chunk in chunk_list or []:
                if isinstance(chunk, str):
                    normalized_list.append(chunk)
                    continue

                if not isinstance(chunk, Mapping):
                    continue

                chunk_name = chunk.get("name")
                if not isinstance(chunk_name, str):
                    continue

                normalized_list.append(chunk_name)
                metadata.setdefault(chunk_name, chunk)

            normalized[bundle_name] = normalized_list

        return normalized, metadata

    @staticmethod
    def _merge_asset_metadata(
        existing: Mapping[str, Mapping[str, object]] | None,
        additions: Mapping[str, Mapping[str, object]],
    ) -> dict[str, Mapping[str, object]]:
        merged = dict(existing) if existing else {}
        for name, chunk in additions.items():
            merged.setdefault(name, chunk)
        return merged
