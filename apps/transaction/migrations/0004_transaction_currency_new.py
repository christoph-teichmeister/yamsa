# Generated by Django 4.1.9 on 2023-05-29 17:04

from django.db import migrations, models
import django.db.models.deletion


def convert_transaction_preferred_currencies(apps, schema_editor):
    OLD_EURO_CONSTANT = 1
    OLD_POUND_STERLING_CONSTANT = 2

    Transaction = apps.get_model("transaction", "Transaction")
    Currency = apps.get_model("currency", "Currency")

    euro_currency, _ = Currency.objects.get_or_create(name="Euro", sign="€")
    pound_currency, _ = Currency.objects.get_or_create(name="Pound Sterling", sign="£")

    for transaction in Transaction.objects.all():
        if transaction.currency == OLD_EURO_CONSTANT:
            transaction.currency_new_id = euro_currency.id

        elif transaction.currency == OLD_POUND_STERLING_CONSTANT:
            transaction.currency_new_id = pound_currency.id

        transaction.save()


class Migration(migrations.Migration):
    dependencies = [
        ("currency", "0002_currency_created_at_currency_created_by_and_more"),
        ("transaction", "0003_alter_transaction_currency"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="currency_new",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="transactions",
                to="currency.currency",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            convert_transaction_preferred_currencies, migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="transaction",
            name="currency",
        ),
        migrations.RenameField(
            model_name="transaction",
            old_name="currency_new",
            new_name="currency",
        ),
    ]