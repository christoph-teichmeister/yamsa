# Generated by Django 5.0.2 on 2024-04-21 14:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0008_alter_user_managers"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="date_joined",
        ),
        migrations.RemoveField(
            model_name="user",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="username",
        ),
        migrations.AlterField(
            model_name="user",
            name="is_staff",
            field=models.BooleanField(
                default=False,
                help_text="Designates whether the user can log into this admin site.",
                verbose_name="Staff Status",
            ),
        ),
    ]
