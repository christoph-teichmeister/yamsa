from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0005_news_room"),
    ]

    operations = [
        migrations.DeleteModel(
            name="NewsComment",
        ),
    ]
