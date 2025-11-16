from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0012_userfriendship"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="wants_to_receive_payment_reminders",
            field=models.BooleanField(default=True),
        ),
    ]
