# Generated by Django 4.1.9 on 2023-10-14 07:50

from django.conf import settings
from django.db import migrations


def populate_new_relation(apps, schema_editor):
    Transaction = apps.get_model("transaction", "Transaction")
    db_alias = schema_editor.connection.alias

    for transaction in Transaction.objects.using(db_alias).all():
        for debitor in transaction.paid_for.all():
            transaction.new_paid_for.add(debitor)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("transaction", "0006_populate_new_m2m_connection"),
    ]

    operations = [
        # migrations.RunPython(populate_new_relation, migrations.RunPython.noop),
    ]