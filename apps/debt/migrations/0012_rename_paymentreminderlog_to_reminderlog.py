from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("debt", "0011_alter_paymentreminderlog_created_by_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="PaymentReminderLog",
            new_name="ReminderLog",
        ),
        migrations.AlterModelOptions(
            name="reminderlog",
            options={
                "verbose_name": "Reminder log",
                "verbose_name_plural": "Reminder logs",
            },
        ),
    ]
