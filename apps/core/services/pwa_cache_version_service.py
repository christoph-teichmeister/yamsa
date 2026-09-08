import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

FALLBACK_VERSION = "dev"

_UNSAFE_CACHE_NAME_CHARS = re.compile(r"[^0-9A-Za-z_-]")
_FINGERPRINT_LENGTH = 12


def resolve_cache_version() -> str:
    """Suffix that separates one release's service worker caches from the previous release's.

    A deploy that leaves this unchanged keeps every browser on the HTML and assets it cached
    before, because the old caches are never purged and network-first only reaches them while the
    device is offline.
    """
    release = settings.RELEASE
    if release:
        return _sanitise(release)

    fingerprint = _asset_fingerprint()
    return f"assets-{fingerprint}" if fingerprint else FALLBACK_VERSION


def _sanitise(value: str) -> str:
    return _UNSAFE_CACHE_NAME_CHARS.sub("-", value)


def _asset_fingerprint() -> str:
    """Hash of the two files that name every asset the service worker precaches.

    Stands in where no release is on offer - a local run, a host that names its builds differently.
    Both files change whenever a rebuild changes what the templates ask for, which is the part a
    stale cache gets wrong.
    """
    digest = hashlib.sha256()
    found = False

    for path in (_staticfiles_manifest_path(), _webpack_stats_path()):
        if path is None:
            continue
        try:
            digest.update(path.read_bytes())
        except OSError:
            continue
        found = True

    return digest.hexdigest()[:_FINGERPRINT_LENGTH] if found else ""


def _staticfiles_manifest_path() -> Path | None:
    manifest_name = getattr(staticfiles_storage, "manifest_name", None)
    if not manifest_name or not settings.STATIC_ROOT:
        return None
    return Path(settings.STATIC_ROOT) / manifest_name


def _webpack_stats_path() -> Path | None:
    stats_file = settings.WEBPACK_LOADER.get("DEFAULT", {}).get("STATS_FILE")
    return Path(stats_file) if stats_file else None
