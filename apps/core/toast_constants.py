from collections.abc import Mapping
from types import MappingProxyType

TOAST_TYPE_CLASSES: Mapping[str, str] = MappingProxyType(
    {
        "info": "toast-primary",
        "success": "toast-success",
        "warning": "toast-warning",
        "error": "toast-danger",
    }
)

INFO_TOAST_CLASS = TOAST_TYPE_CLASSES["info"]
SUCCESS_TOAST_CLASS = TOAST_TYPE_CLASSES["success"]
WARNING_TOAST_CLASS = TOAST_TYPE_CLASSES["warning"]
ERROR_TOAST_CLASS = TOAST_TYPE_CLASSES["error"]

__all__ = [
    "ERROR_TOAST_CLASS",
    "INFO_TOAST_CLASS",
    "SUCCESS_TOAST_CLASS",
    "TOAST_TYPE_CLASSES",
    "WARNING_TOAST_CLASS",
]
