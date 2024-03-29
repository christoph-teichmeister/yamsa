# Generated by Django 4.1.7 on 2023-05-23 20:14

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("debt", "0001_initial"),
        ("room", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
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
                        db_index=True,
                        default=django.utils.timezone.now,
                        verbose_name="Created at",
                    ),
                ),
                (
                    "lastmodified_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        verbose_name="Last modified at",
                    ),
                ),
                ("description", models.TextField(max_length=500)),
                ("value", models.DecimalField(decimal_places=2, max_digits=10)),
                ("settled", models.BooleanField(default=False)),
                ("settled_at", models.DateField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "lastmodified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_lastmodified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last modified by",
                    ),
                ),
                (
                    "paid_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="made_transactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "paid_for",
                    models.ManyToManyField(through="debt.Debt", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="room.room",
                    ),
                ),
            ],
            options={
                "verbose_name": "Transaction",
                "verbose_name_plural": "Transaction",
                "ordering": ("-id",),
            },
        ),
    ]
