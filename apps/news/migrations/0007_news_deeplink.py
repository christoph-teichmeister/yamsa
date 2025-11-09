from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0006_delete_newscomment"),
    ]

    operations = [
        migrations.AddField(
            model_name="news",
            name="deeplink",
            field=models.CharField(blank=True, max_length=512),
        ),
    ]
