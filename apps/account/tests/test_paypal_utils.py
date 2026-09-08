import pytest
from django.core.exceptions import ValidationError

from apps.account.utils.paypal import normalize_paypal_me_username


class TestNormalizePaypalMeUsername:
    @pytest.mark.parametrize(
        "raw_value",
        [
            "creditorname",
            "  creditorname  ",
            "@creditorname",
            "@ creditorname",
            "paypal.me/creditorname",
            "www.paypal.me/creditorname",
            "https://paypal.me/creditorname",
            "https://www.paypal.me/creditorname/",
            "http://www.paypal.me/creditorname",
            "PayPal.Me/creditorname",
            "paypal.com/paypalme/creditorname",
            "https://www.paypal.com/paypalme/creditorname",
            "https://www.paypal.me/creditorname?locale.x=de_DE",
            # The amount the debt page appends is part of the link, never part of the handle.
            "https://www.paypal.com/paypalme/creditorname/42.50EUR",
        ],
    )
    def test_paste_shapes_reduce_to_the_bare_handle(self, raw_value):
        assert normalize_paypal_me_username(raw_value) == "creditorname"

    @pytest.mark.parametrize("raw_value", [None, "", "   ", "@", "https://paypal.me/"])
    def test_blank_input_clears_the_field(self, raw_value):
        assert normalize_paypal_me_username(raw_value) is None

    @pytest.mark.parametrize(
        "raw_value",
        [
            "creditor name",
            "creditor_name",
            "creditor-name",
            "creditor.name",
            "creditör",
            "a" * 21,
        ],
    )
    def test_values_that_cannot_be_a_handle_are_rejected(self, raw_value):
        with pytest.raises(ValidationError):
            normalize_paypal_me_username(raw_value)

    def test_case_is_kept(self):
        """PayPal.Me resolves case-insensitively, but the profile shows back what the user typed."""
        assert normalize_paypal_me_username("CreditorName") == "CreditorName"
