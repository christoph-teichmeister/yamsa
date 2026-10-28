from collections.abc import Callable

import pytest

from apps.account.handlers.commands.remove_user_from_room import handle_remove_user_from_room
from apps.account.handlers.commands.send_forgot_password_email import handle_send_forgot_password_email
from apps.account.handlers.commands.send_invitation_email import handle_send_invitation_email
from apps.account.handlers.commands.send_post_register_email import handle_send_post_register_mail
from apps.room.handlers.commands.delete_room import handle_delete_room
from apps.room.handlers.events.cleanup_receipts_on_room_deleted import delete_receipt_files_on_room_deleted
from apps.room.handlers.events.notify_on_room_deleted import send_notification_on_room_deleted
from apps.room.handlers.events.notify_on_room_status_changed import send_notification_on_room_status_changed
from apps.room.handlers.events.notify_on_user_connection_to_room_created import (
    send_email_on_user_connection_to_room_created,
    send_notification_on_user_connection_to_room_created,
)

# Mail/push/storage I/O handlers: the runner must not hold a DB transaction open around them (#333).
IO_HANDLERS = [
    handle_send_forgot_password_email,
    handle_send_invitation_email,
    handle_send_post_register_mail,
    delete_receipt_files_on_room_deleted,
    send_notification_on_room_deleted,
    send_notification_on_room_status_changed,
    send_notification_on_user_connection_to_room_created,
    send_email_on_user_connection_to_room_created,
]

# Handlers whose DB writes the triggering change depends on stay atomic.
DB_HANDLERS = [handle_delete_room, handle_remove_user_from_room]


class TestHandlerAtomicity:
    @pytest.mark.parametrize("handler", IO_HANDLERS, ids=lambda handler: handler.__name__)
    def test_io_handler_runs_outside_a_transaction(self, handler: Callable) -> None:
        assert handler.atomic is False

    @pytest.mark.parametrize("handler", DB_HANDLERS, ids=lambda handler: handler.__name__)
    def test_db_handler_stays_atomic(self, handler: Callable) -> None:
        assert handler.atomic is True
