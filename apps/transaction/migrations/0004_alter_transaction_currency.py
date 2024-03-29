# Generated by Django 4.1.9 on 2023-05-30 15:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("currency", "0001_initial"),
        ("transaction", "0003_alter_transaction_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="currency",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="transactions",
                to="currency.currency",
            ),
        ),
    ]
