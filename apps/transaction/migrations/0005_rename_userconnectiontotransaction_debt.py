# Generated by Django 4.1.7 on 2023-05-21 17:36

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("transaction", "0004_userconnectiontotransaction_settled_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="UserConnectionToTransaction",
            new_name="Debt",
        ),
    ]
