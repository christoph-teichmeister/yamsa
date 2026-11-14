from apps.config.settings.base import env

# AMBIENT TOOLBOX
# ------------------------------------------------------------------------------

# Test structure validator allowlist
# https://ambient-toolbox.readthedocs.io/en/latest/features/tests.html#test-structure-validator
TEST_STRUCTURE_VALIDATOR_FILE_WHITELIST_FUTURE_GLOB_PATTERNS = [
    "user_factory",
    "superuser_factory",
    "guest_user_factory",
    "user_passkey_factory",
    "capture_handler",
    "dummy_command",
    "dummy_event",
    "dummy_instance",
    "dummy_context",
    "dummy_meta",
    "toast_urls",
    "room_factory",
    "user_connection_to_room_factory",
    "child_transaction_factory",
    "parent_transaction_factory",
]
TEST_STRUCTURE_VALIDATOR_FILE_WHITELIST = [
    "factories",
    "conftest",
    "constants",
    *TEST_STRUCTURE_VALIDATOR_FILE_WHITELIST_FUTURE_GLOB_PATTERNS,
]

# Directories skipped by validators such as `validate_test_structure`.
TEST_STRUCTURE_VALIDATOR_IGNORED_DIRECTORY_LIST = [
    ".venv",
]


# WEBPUSH
# ------------------------------------------------------------------------------
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": env("VAPID_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": env("VAPID_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": env("VAPID_ADMIN_EMAIL"),
}
WEBPUSH_NOTIFICATION_CLASS = "apps.webpush.dataclasses.Notification"

MAINTENANCE = env("MAINTENANCE")
