# Generated by Django 4.1.9 on 2023-05-29 15:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("room", "0003_room_preferred_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="preferred_currency",
            field=models.SmallIntegerField(
                choices=[(1, "€ - Euro"), (2, "£ - Pound Sterling")], default=1
            ),
        ),
    ]
