from decimal import Decimal
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.formats import date_format, number_format
from django.utils.translation import gettext as _

from apps.account.models import User
from apps.transaction.models import ParentTransaction, TransactionChange


def snapshot(parent_transaction: ParentTransaction) -> dict[str, Any]:
    """The values of a transaction a history entry can name, read before and after an edit.

    Read from a fresh query: the edit form mutates the instance it is given while validating.
    """
    parent = ParentTransaction.objects.select_related("paid_by", "category", "currency").get(pk=parent_transaction.pk)
    split: dict[int, tuple[str, Decimal]] = {}
    for child in parent.child_transactions.select_related("paid_for"):
        name, value = split.get(child.paid_for_id, (child.paid_for.name, Decimal(0)))
        split[child.paid_for_id] = (name, value + child.value)
    return {
        "description": parent.description or "",
        "notes": parent.further_notes or "",
        "payer": parent.paid_by.name,
        "category": parent.category.name,
        "currency": parent.currency.sign,
        "date": parent.paid_at,
        "amount": sum((value for _name, value in split.values()), Decimal(0)),
        "sign": parent.currency.sign,
        "split": split,
    }


def diff(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for field in ("amount", "payer", "category", "currency", "description", "notes"):
        if before[field] != after[field]:
            entry: dict[str, Any] = {"field": field, "old": str(before[field]), "new": str(after[field])}
            if field == "amount":
                entry["sign"] = after["sign"]
            changes.append(entry)
    if before["date"] != after["date"]:
        changes.append({"field": "date", "old": before["date"].isoformat(), "new": after["date"].isoformat()})

    return changes + _split_changes(before, after)


def _split_changes(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for user_id in sorted(before["split"].keys() | after["split"].keys()):
        old = before["split"].get(user_id)
        new = after["split"].get(user_id)
        if old != new:
            changes.append(
                {
                    "field": "split",
                    "who": (new or old)[0],
                    "old": str(old[1]) if old else None,
                    "new": str(new[1]) if new else None,
                    "sign": after["sign"],
                }
            )
    return changes


def record(
    parent_transaction: ParentTransaction,
    user: User,
    kind: str,
    detail: str = "",
    changes: list[dict[str, Any]] | None = None,
) -> TransactionChange:
    return TransactionChange.objects.create(
        parent_transaction=parent_transaction, user=user, kind=kind, detail=detail, changes=changes or []
    )


def _money(value: str, sign: str) -> str:
    return f"{number_format(Decimal(value), decimal_pos=2, use_l10n=True, force_grouping=True)}{sign}"


def _moment(value: str) -> str:
    return date_format(timezone.localtime(parse_datetime(value)), "SHORT_DATETIME_FORMAT")


def describe_headline(change: TransactionChange) -> str:
    who = change.user.name if change.user else _("Someone")
    match change.kind:
        case TransactionChange.Kind.CREATED:
            return _("%(user)s created this expense") % {"user": who}
        case TransactionChange.Kind.RECEIPT_ADDED:
            return _("%(user)s added the receipt %(name)s") % {"user": who, "name": change.detail}
        case TransactionChange.Kind.RECEIPT_REMOVED:
            return _("%(user)s removed the receipt %(name)s") % {"user": who, "name": change.detail}
    return _("%(user)s edited this expense") % {"user": who}


def describe_lines(change: TransactionChange) -> list[str]:
    return [_describe_entry(entry) for entry in change.changes]


def _describe_entry(entry: dict[str, Any]) -> str:
    field, old, new = entry["field"], entry["old"], entry["new"]
    if field == "split":
        who, sign = entry["who"], entry["sign"]
        if old is None:
            return _("%(who)s added to the split: %(new)s") % {"who": who, "new": _money(new, sign)}
        if new is None:
            return _("%(who)s removed from the split (was %(old)s)") % {"who": who, "old": _money(old, sign)}
        return _("Share of %(who)s: %(old)s → %(new)s") % {
            "who": who,
            "old": _money(old, sign),
            "new": _money(new, sign),
        }
    if field == "amount":
        old, new = _money(old, entry["sign"]), _money(new, entry["sign"])
    elif field == "date":
        old, new = _moment(old), _moment(new)
    label = {
        "amount": _("Amount: %(old)s → %(new)s"),
        "payer": _("Paid by: %(old)s → %(new)s"),
        "category": _("Category: %(old)s → %(new)s"),
        "currency": _("Currency: %(old)s → %(new)s"),
        "description": _("Description: %(old)s → %(new)s"),
        "notes": _("Notes: %(old)s → %(new)s"),
        "date": _("Date: %(old)s → %(new)s"),
    }[field]
    return label % {"old": old or "-", "new": new or "-"}
