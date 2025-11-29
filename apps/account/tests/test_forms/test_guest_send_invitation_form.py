from apps.account.forms.guest_send_invitation_form import GuestSendInvitationEmailForm
from apps.account.models import User


class TestGuestSendInvitationEmailForm:
    form_class = GuestSendInvitationEmailForm

    def test_new_email_is_set(self, user):
        new_email = "new_email@local.local"
        form = self.form_class(instance=user, data={"email": new_email})
        assert form.is_valid()

        form.save()

        user.refresh_from_db()

        assert user.email == new_email

    def test_form_raises_error_if_email_already_exists(self, user, superuser):
        form = self.form_class(instance=user, data={"email": superuser.email})
        assert not form.is_valid()

        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_ALREADY_EXISTS.format(email=superuser.email)

    def test_case_insensitive_email_duplicate(self, user, superuser):
        uppercased_email = superuser.email.upper()
        form = self.form_class(instance=user, data={"email": uppercased_email})
        assert not form.is_valid()

        expected_email = User.objects.normalize_email(uppercased_email)
        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_ALREADY_EXISTS.format(email=expected_email)
