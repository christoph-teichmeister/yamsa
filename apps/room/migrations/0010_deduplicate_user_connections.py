from django.db import migrations
from django.db.models import Count, Min


def deduplicate_user_connections(apps, schema_editor):
    UserConnectionToRoom = apps.get_model("room", "UserConnectionToRoom")

    duplicated_pairs = (
        UserConnectionToRoom.objects.values("user_id", "room_id")
        .annotate(connection_count=Count("id"), kept_id=Min("id"))
        .filter(connection_count__gt=1)
    )

    for pair in duplicated_pairs:
        duplicates = UserConnectionToRoom.objects.filter(
            user_id=pair["user_id"],
            room_id=pair["room_id"],
        ).exclude(id=pair["kept_id"])

        # A room counts as seen if any of the merged rows had been seen, so collapsing them
        # never resurfaces a room the user already visited.
        if duplicates.filter(user_has_seen_this_room=True).exists():
            UserConnectionToRoom.objects.filter(id=pair["kept_id"]).update(user_has_seen_this_room=True)

        duplicates.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("room", "0009_room_share_hash"),
    ]

    operations = [
        migrations.RunPython(deduplicate_user_connections, migrations.RunPython.noop),
    ]
