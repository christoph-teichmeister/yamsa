import re
from pathlib import Path

from django.conf import settings

OUTBOX_JS = Path(settings.APPS_DIR) / "static/js/outbox.js"
SERVICE_WORKER = Path(settings.APPS_DIR) / "core/templates/core/pwa/serviceworker.js"
SHARED_CONSTANTS = ("OUTBOX_DATABASE", "OUTBOX_STORE", "OUTBOX_VERSION", "OUTBOX_SYNC_TAG")


def _constant(source: str, name: str) -> str:
    match = re.search(rf"const {name}\s*=\s*([^;\n]+)", source)
    assert match, f"{name} not found"
    return match.group(1).strip().strip("\"'")


class TestOutboxConstantsAgree:
    # The worker is a template served outside webpack and cannot import outbox.js, so it keeps
    # copies; a drift would make page and worker read different IndexedDB stores.
    def test_service_worker_copies_match_outbox_module(self) -> None:
        module, worker = OUTBOX_JS.read_text(), SERVICE_WORKER.read_text()

        for name in SHARED_CONSTANTS:
            assert _constant(worker, name) == _constant(module, name), name
