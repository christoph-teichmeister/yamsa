from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0013_user_payment_reminder_preferences"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="wants_to_receive_room_reminders",
            field=models.BooleanField(default=True),
        ),
    ]
