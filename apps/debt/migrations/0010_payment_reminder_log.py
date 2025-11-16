from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("debt", "0009_debt_created_at_debt_created_by_debt_lastmodified_at_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentReminderLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "reminder_type",
                    models.CharField(
                        choices=[("inactive_debt", "Inactive debt reminder")],
                        default="inactive_debt",
                        max_length=50,
                    ),
                ),
                ("recipients", models.JSONField(default=list)),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, verbose_name="Created at"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="debt_paymentreminderlog_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "lastmodified_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now, verbose_name="Last modified at"
                    ),
                ),
                (
                    "lastmodified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="debt_paymentreminderlog_lastmodified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last modified by",
                    ),
                ),
            ],
            options={
                "verbose_name": "Payment reminder log",
                "verbose_name_plural": "Payment reminder logs",
            },
        ),
    ]
