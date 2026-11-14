import pytest

from apps.transaction.forms.transaction_create_form import receipt_name_matches_content_type


class TestReceiptNameMatchesContentType:
    @pytest.mark.parametrize(
        ("name", "content_type"),
        [
            ("bill.pdf", "application/pdf"),
            ("photo.JPG", "image/jpeg"),
            ("photo.jpeg", "image/jpeg"),
            ("shot.png", "image/png"),
            ("anim.gif", "image/gif"),
            ("pic.webp", "image/webp"),
        ],
    )
    def test_matching_pairs_pass(self, name: str, content_type: str) -> None:
        assert receipt_name_matches_content_type(name, content_type)

    @pytest.mark.parametrize(
        ("name", "content_type"),
        [
            ("page.html", "image/png"),
            ("script.svg", "image/png"),
            ("bill.pdf", "image/png"),
            ("noextension", "application/pdf"),
            ("bill.pdf.exe", "application/pdf"),
        ],
    )
    def test_mismatching_or_unlisted_pairs_fail(self, name: str, content_type: str) -> None:
        assert not receipt_name_matches_content_type(name, content_type)
