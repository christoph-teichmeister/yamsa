# Generated by Django 4.1.9 on 2023-05-28 09:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="currency",
            field=models.SmallIntegerField(
                choices=[(1, "Euro (€)"), (2, "Pound Sterling (£)")], default=1
            ),
        ),
    ]
