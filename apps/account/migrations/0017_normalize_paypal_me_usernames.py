import re

from django.db import migrations

# Frozen copy of apps.account.utils.paypal as of this migration: a migration must not import live app
# code, which keeps changing (or disappearing) while this one has to replay the same way forever.
_URL_PREFIX = re.compile(r"^(?:https?://)?(?:www\.)?paypal(?:\.me/|\.com/paypalme/)", flags=re.IGNORECASE)
_HANDLE = re.compile(r"^[A-Za-z0-9]{1,20}$")


def normalize_paypal_me_username(value):
    """Return the bare handle, None for blank, or raise ValueError for something that cannot be one."""
    normalized = _URL_PREFIX.sub("", value.strip())
    normalized = re.split(r"[?#/]", normalized, maxsplit=1)[0].strip().lstrip("@").strip()
    if not normalized:
        return None
    if not _HANDLE.match(normalized):
        raise ValueError(value)
    return normalized


def normalize_stored_paypal_me_usernames(apps, schema_editor):
    """Bring stored handles in line with what User.clean() now accepts.

    Not optional: CleanOnSaveMixin runs full_clean() on every save, so a row the new rule rejects
    would make unrelated profile saves fail. A value that survives normalization but is still no
    valid handle cannot resolve to a PayPal profile, so it is cleared - the button then stays
    hidden instead of offering a link that 404s.
    """
    User = apps.get_model("account", "User")
    db_alias = schema_editor.connection.alias

    for user in User.objects.using(db_alias).exclude(paypal_me_username__isnull=True):
        try:
            normalized_username = normalize_paypal_me_username(user.paypal_me_username)
        except ValueError:
            normalized_username = None

        if normalized_username == user.paypal_me_username:
            continue

        user.paypal_me_username = normalized_username
        user.save(update_fields=["paypal_me_username"])


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0016_alter_user_profile_picture"),
    ]

    operations = [
        # No backward method: the original spelling of a cleared or rewritten handle is not
        # recoverable, and restoring it would only reinstate a link that does not work.
        migrations.RunPython(normalize_stored_paypal_me_usernames, migrations.RunPython.noop),
    ]
