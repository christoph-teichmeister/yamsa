import uuid

from apps.currency.models import Currency
from apps.importer.constants import SESSION_KEY_PREFIX


def _session_key(token: str) -> str:
    return f"{SESSION_KEY_PREFIX}:{token}"


def store_parsed_import(session, payload: dict) -> str:
    """Park a parsed file under its own token so a second upload tab cannot overwrite the first."""
    token = uuid.uuid4().hex
    session[_session_key(token)] = payload
    return token


def read_parsed_import(session, token: str) -> dict | None:
    if not token:
        return None
    return session.get(_session_key(token))


def pop_parsed_import(session, token: str) -> dict | None:
    return session.pop(_session_key(token), None)


def resolve_currencies_by_code(codes) -> dict[str, Currency | None]:
    """
    Map source currency codes onto Currency rows.

    Currency.code carries no unique constraint, so .get() could raise MultipleObjectsReturned.
    A code with no row maps to None; callers decide whether to warn or substitute.
    """
    matches = {}
    for code in codes:
        matches[code] = Currency.objects.filter(code__iexact=code.strip()).order_by("id").first()
    return matches
