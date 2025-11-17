from __future__ import annotations

from collections.abc import Mapping

TOAST_TYPE_CLASSES: Mapping[str, str] = {
    "info": "text-bg-primary bg-gradient",
    "success": "text-bg-success bg-gradient",
    "warning": "text-bg-warning bg-gradient",
    "error": "text-bg-danger bg-gradient",
}

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
