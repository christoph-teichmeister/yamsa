import uuid
from decimal import Decimal

from django.conf import settings
from django.db.models import Model
from django.http import HttpRequest
from django.utils.formats import number_format


def determine_upload_to(instance: Model, filename: str) -> str:
    """Return an upload path that keeps the folder structure but guarantees a unique filename."""
    base_path = f"{instance._meta.app_label}/{instance._meta.model_name}"
    if instance.UPLOAD_FOLDER_NAME is not None:
        base_path = f"{base_path}/{instance.UPLOAD_FOLDER_NAME}"
    unique_filename = f"{uuid.uuid4()}-{filename}"
    return f"{base_path}/{unique_filename}"


def format_number_with_thousands(value: Decimal | int | float) -> str:
    """Render a number with the locale's thousands separator and exactly two decimals.

    Single source for the rule: the ``format_with_thousands`` template filter and the views that
    format amounts outside a template both call this, so a legend and a chart label on the same
    page cannot drift apart.
    """
    return number_format(value, decimal_pos=2, use_l10n=True, force_grouping=True)


def get_client_ip(request: HttpRequest) -> str | None:
    """Return the client IP, trusting only as many X-Forwarded-For hops as ``TRUSTED_PROXY_COUNT`` names.

    Every proxy appends the address it saw to the right of the header, so the entry ``TRUSTED_PROXY_COUNT``
    from the right is the one our own outermost proxy wrote; anything a client prepends sits further left and
    is ignored. With the default of 0 the header is not read at all and ``REMOTE_ADDR`` is used, which is not
    spoofable but is the proxy's address when the app runs behind one.
    """
    proxy_count = settings.TRUSTED_PROXY_COUNT
    if proxy_count:
        hops = [hop.strip() for hop in request.headers.get("x-forwarded-for", "").split(",") if hop.strip()]
        if len(hops) >= proxy_count:
            return hops[-proxy_count]
    return request.META.get("REMOTE_ADDR")
