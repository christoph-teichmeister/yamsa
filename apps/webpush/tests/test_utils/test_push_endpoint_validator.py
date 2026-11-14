import pytest

from apps.webpush.validators import is_safe_push_endpoint


class TestIsSafePushEndpoint:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://fcm.googleapis.com/fcm/send/abc",
            "https://updates.push.services.mozilla.com/wpush/v2/abc",
            "https://8.8.8.8/push",
        ],
    )
    def test_public_https_endpoints_pass(self, endpoint: str) -> None:
        assert is_safe_push_endpoint(endpoint)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://fcm.googleapis.com/fcm/send/abc",
            "https://localhost/push",
            "https://127.0.0.1/push",
            "https://10.0.0.5/push",
            "https://192.168.1.1/push",
            "https://169.254.169.254/latest/meta-data",
            "https://[::1]/push",
            "https://printer.local/push",
            "https://intranet/push",
            "ftp://example.com/push",
            "https:///push",
        ],
    )
    def test_internal_or_non_https_endpoints_fail(self, endpoint: str) -> None:
        assert not is_safe_push_endpoint(endpoint)
