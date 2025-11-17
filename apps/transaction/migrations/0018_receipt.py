# Generated manually since migrations must be written without running manage.py in this environment
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.utils.translation


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0017_parenttransaction_category"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Receipt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        db_index=True,
                        verbose_name=django.utils.translation.gettext_lazy("Created at"),
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_receipt_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name=django.utils.translation.gettext_lazy("Created by"),
                    ),
                ),
                (
                    "lastmodified_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        db_index=True,
                        verbose_name=django.utils.translation.gettext_lazy("Last modified at"),
                    ),
                ),
                (
                    "lastmodified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_receipt_lastmodified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name=django.utils.translation.gettext_lazy("Last modified by"),
                    ),
                ),
                (
                    "parent_transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receipts",
                        to="transaction.parenttransaction",
                    ),
                ),
                (
                    "file",
                    models.FileField(upload_to="receipts/%Y/%m/%d/"),
                ),
                (
                    "original_name",
                    models.CharField(max_length=255),
                ),
                (
                    "content_type",
                    models.CharField(max_length=255),
                ),
                (
                    "size",
                    models.PositiveBigIntegerField(),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploaded_receipts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Transaction receipt",
                "verbose_name_plural": "Transaction receipts",
            },
        ),
    ]
