from decimal import Decimal

from django.test import TestCase
from model_bakery import baker

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import Category, ChildTransaction


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


class TransactionEditFormTotalValueTests(TestCase):
    def setUp(self):
        self.payer = baker.make_recipe("apps.account.tests.user")
        self.participant = baker.make_recipe("apps.account.tests.user")
        self.room = baker.make_recipe("apps.room.tests.room")
        self.room.users.add(self.payer, self.participant)

        self.parent_transaction = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.payer,
        )
        ChildTransaction.objects.create(
            parent_transaction=self.parent_transaction,
            paid_for=self.payer,
            value=Decimal("10.00"),
        )
        ChildTransaction.objects.create(
            parent_transaction=self.parent_transaction,
            paid_for=self.participant,
            value=Decimal("20.00"),
        )

    def _base_form_data(self, total_value):
        child_transactions = list(self.parent_transaction.child_transactions.order_by("-id"))
        return {
            "description": self.parent_transaction.description,
            "further_notes": self.parent_transaction.further_notes or "",
            "paid_by": self.parent_transaction.paid_by.id,
            "paid_at": self.parent_transaction.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
            "currency": self.parent_transaction.currency.id,
            "category": self.parent_transaction.category.id,
            "paid_for": [ct.paid_for.id for ct in child_transactions],
            "value": [str(ct.value) for ct in child_transactions],
            "child_transaction_id": [ct.id for ct in child_transactions],
            "total_value": total_value,
        }

    def test_total_value_field_exposes_correct_initial(self):
        form = TransactionEditForm(instance=self.parent_transaction)

        self.assertIn("total_value", form.fields)
        self.assertEqual(form.initial["total_value"], self.parent_transaction.value)

    def test_rebalances_shares_when_total_changes(self):
        data = self._base_form_data(total_value="60.00")
        form = TransactionEditForm(data=data, instance=self.parent_transaction)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["total_value"], Decimal("60.00"))
        self.assertEqual(form.cleaned_data["value"], [Decimal("30.00"), Decimal("30.00")])

    def test_propagates_value_sum_when_shares_rebalanced(self):
        data = self._base_form_data(total_value=str(self.parent_transaction.value))
        data["value"] = ["15.00", "25.00"]
        form = TransactionEditForm(data=data, instance=self.parent_transaction)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["total_value"], Decimal("40.00"))
        self.assertEqual(form.cleaned_data["value"], [Decimal("15.00"), Decimal("25.00")])
