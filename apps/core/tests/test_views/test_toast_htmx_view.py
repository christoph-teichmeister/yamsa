from django.urls import reverse

from apps.core.toast_constants import TOAST_TYPE_CLASSES


def test_toast_htmx_view_returns_toast_payload(client):
    response = client.get(reverse("core:toast"), {"toast_message": "Hello", "toast_type": "warning"})
    response.render()

    assert response.status_code == 200
    assert "shared_partials/toast.html" in [template.name for template in response.templates]

    queued_toasts = response.context_data["queued_toasts"]
    assert queued_toasts == [
        {"message": "Hello", "type": TOAST_TYPE_CLASSES["warning"]},
    ]


def test_toast_htmx_view_defaults_to_info_for_unknown_type(client):
    response = client.get(reverse("core:toast"), {"toast_message": "Hi", "toast_type": "missing"})
    response.render()

    toast_entry = response.context_data["queued_toasts"][0]
    assert toast_entry["type"] == TOAST_TYPE_CLASSES["info"]


def test_toast_htmx_view_without_message_skips_toasts(client):
    response = client.get(reverse("core:toast"))
    response.render()

    assert response.context_data["queued_toasts"] == []


def test_toast_type_classes_match_expected_styles():
    expected_classes = {
        "info": "toast-primary",
        "success": "toast-success",
        "warning": "toast-warning",
        "error": "toast-danger",
    }

    assert dict(TOAST_TYPE_CLASSES) == expected_classes
