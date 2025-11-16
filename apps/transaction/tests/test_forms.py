from django.test import TestCase
from model_bakery import baker

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import Category


class TransactionFormTests(TestCase):
    def test_create_form_exposes_category_field_ordered(self):
        form = TransactionCreateForm()
        self.assertIn("category", form.fields)
        queryset = list(form.fields["category"].queryset)
        self.assertGreaterEqual(len(queryset), 1)
        self.assertEqual(queryset[0].slug, "accommodation")

    def test_edit_form_initial_category_matches_instance(self):
        category = Category.objects.get(slug="groceries")
        parent_transaction = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            category=category,
        )
        form = TransactionEditForm(instance=parent_transaction)

        self.assertEqual(form.initial["category"], category.pk)
