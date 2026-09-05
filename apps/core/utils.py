import uuid
from decimal import Decimal

from django.utils.formats import number_format


def determine_upload_to(instance, filename: str):
    """Return an upload path that keeps the folder structure but guarantees a unique filename."""
    base_path = f"{instance._meta.app_label}/{instance._meta.model_name}"
    if instance.UPLOAD_FOLDER_NAME is not None:
        base_path = f"{base_path}/{instance.UPLOAD_FOLDER_NAME}"
    unique_filename = f"{uuid.uuid4()}-{filename}"
    return f"{base_path}/{unique_filename}"


def format_number_with_thousands(value: Decimal | int | float) -> str:
    """
    Render a number with the locale's thousands separator and exactly two decimals.

    Single source for the rule: the ``format_with_thousands`` template filter and the views that
    format amounts outside a template both call this, so a legend and a chart label on the same
    page cannot drift apart.
    """
    return number_format(value, decimal_pos=2, use_l10n=True, force_grouping=True)
