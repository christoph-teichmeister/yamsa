# Generated by Django 4.1.7 on 2023-05-21 17:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0003_remove_transaction_paid_for_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userconnectiontotransaction",
            name="settled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userconnectiontotransaction",
            name="settled_at",
            field=models.DateField(blank=True, null=True),
        ),
    ]
