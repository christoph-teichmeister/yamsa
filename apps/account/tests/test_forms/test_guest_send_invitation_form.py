from apps.account.forms.guest_send_invitation_form import GuestSendInvitationEmailForm
from apps.core.tests.setup import BaseTestSetUp


class GuestSendInvitationEmailFormTestCase(BaseTestSetUp):
    form = GuestSendInvitationEmailForm

    def test_new_email_is_set(self):
        new_email = "new_email@local.local"
        new_data = {"email": new_email}

        form = self.form(instance=self.user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()

        self.user.refresh_from_db()

        self.assertEqual(self.user.email, new_email)

    def test_form_raises_error_if_email_already_exists(self):
        form = self.form(instance=self.user, data={"email": self.superuser.email})
        self.assertFalse(form.is_valid())

        self.assertEqual(form.errors["email"][0], form.ExceptionMessage.EMAIL_ALREADY_EXISTS)
