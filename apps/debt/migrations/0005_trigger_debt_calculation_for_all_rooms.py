# Generated by Django 4.1.9 on 2023-10-08 13:36

from django.conf import settings
from django.db import migrations

from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionCreated


def triggers_debt_calculation_for_all_rooms(apps, schema_editor):
    Room = apps.get_model("room", "Room")

    db_alias = schema_editor.connection.alias

    for room in Room.objects.using(db_alias).all():
        transaction = room.transactions.first()

        handle_message(ParentTransactionCreated(context_data={"transaction": transaction}))


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("debt", "0004_translate_old_debts_to_new_debts"),
    ]

    operations = [
        migrations.RunPython(triggers_debt_calculation_for_all_rooms, migrations.RunPython.noop),
    ]