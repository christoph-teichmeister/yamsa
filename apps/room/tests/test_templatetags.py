"""
Tests for room templatetags, specifically the format_with_thousands filter.
"""
from decimal import Decimal

from django.test import TestCase, override_settings
from django.template import Template, Context

from apps.room.templatetags.room_tags import format_with_thousands


class FormatWithThousandsFilterTestCase(TestCase):
    """Test cases for the format_with_thousands template filter."""

    def test_integer_with_thousands_german_locale(self):
        """Test integer formatting with German locale."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(1234)
            self.assertEqual(result, "1.234,00")

    def test_decimal_with_thousands_german_locale(self):
        """Test decimal formatting with German locale."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(1234.56)
            self.assertEqual(result, "1.234,56")

    def test_large_number_german_locale(self):
        """Test large number formatting with German locale."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(1000000.99)
            self.assertEqual(result, "1.000.000,99")

    def test_integer_with_thousands_english_locale(self):
        """Test integer formatting with English locale."""
        with override_settings(LANGUAGE_CODE='en-us', USE_L10N=True):
            result = format_with_thousands(1234)
            self.assertEqual(result, "1,234.00")

    def test_decimal_with_thousands_english_locale(self):
        """Test decimal formatting with English locale."""
        with override_settings(LANGUAGE_CODE='en-us', USE_L10N=True):
            result = format_with_thousands(1234.56)
            self.assertEqual(result, "1,234.56")

    def test_large_number_english_locale(self):
        """Test large number formatting with English locale."""
        with override_settings(LANGUAGE_CODE='en-us', USE_L10N=True):
            result = format_with_thousands(1000000.99)
            self.assertEqual(result, "1,000,000.99")

    def test_small_number_no_thousands(self):
        """Test small number that doesn't need thousands separator."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(999)
            self.assertEqual(result, "999,00")

    def test_decimal_type_input(self):
        """Test with Decimal type input."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(Decimal("1234.56"))
            self.assertEqual(result, "1.234,56")

    def test_string_numeric_input(self):
        """Test with string numeric input."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands("1234.56")
            self.assertEqual(result, "1.234,56")

    def test_zero_value(self):
        """Test with zero value."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(0)
            self.assertEqual(result, "0,00")

    def test_negative_number(self):
        """Test with negative number."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(-1234.56)
            self.assertEqual(result, "-1.234,56")

    def test_invalid_string_input(self):
        """Test with invalid string input - should return original value."""
        result = format_with_thousands("not a number")
        self.assertEqual(result, "not a number")

    def test_none_input(self):
        """Test with None input - should return 'None'."""
        result = format_with_thousands(None)
        self.assertEqual(result, "None")

    def test_in_template(self):
        """Test filter usage in a Django template."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            template = Template("{% load room_tags %}{{ value|format_with_thousands }}")
            context = Context({"value": 1234.56})
            result = template.render(context)
            self.assertEqual(result, "1.234,56")

    def test_in_template_english(self):
        """Test filter usage in a Django template with English locale."""
        with override_settings(LANGUAGE_CODE='en-us', USE_L10N=True):
            template = Template("{% load room_tags %}{{ value|format_with_thousands }}")
            context = Context({"value": 1234.56})
            result = template.render(context)
            self.assertEqual(result, "1,234.56")

    def test_very_large_number(self):
        """Test with very large number (millions)."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(123456789.99)
            self.assertEqual(result, "123.456.789,99")

    def test_fractional_number(self):
        """Test with number less than 1."""
        with override_settings(LANGUAGE_CODE='de', USE_L10N=True):
            result = format_with_thousands(0.99)
            self.assertEqual(result, "0,99")

    def test_french_locale(self):
        """Test with French locale."""
        with override_settings(LANGUAGE_CODE='fr', USE_L10N=True):
            result = format_with_thousands(1234.56)
            # French uses non-breaking space as thousand separator and comma as decimal
            # The result should contain a comma and thousands separator
            self.assertIn(",56", result)
            self.assertIn("234", result)  # Check for part of the number
