from django.test import Client

from apps.importer.constants import MAX_PARKED_IMPORTS
from apps.importer.session import read_parsed_import, store_parsed_import


class TestImportSessionRetention:
    """Abandoned previews must not pile up in the session (cached_db rows are size-sensitive)."""

    def test_only_the_most_recent_previews_are_kept(self, db: None, authenticated_client: Client) -> None:
        session = authenticated_client.session
        tokens = [store_parsed_import(session, {"people": [str(index)]}) for index in range(MAX_PARKED_IMPORTS + 2)]
        session.save()

        kept = [token for token in tokens if read_parsed_import(authenticated_client.session, token) is not None]

        assert kept == tokens[-MAX_PARKED_IMPORTS:]
