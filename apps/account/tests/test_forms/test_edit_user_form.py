from apps.account.forms import EditUserForm
from apps.core.tests.setup import BaseTestSetUp
from apps.webpush.models import WebpushInformation


class EditUserFormTestCase(BaseTestSetUp):
    form = EditUserForm

    def test_regular(self):
        new_data = {
            "username": "new_username",
            "name": "new_name",
            "email": "new_email@local.local",
            "paypal_me_username": "new_paypal_me_username",
            "wants_to_receive_webpush_notifications": True,
        }

        form = self.form(instance=self.user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()
        self.user.refresh_from_db()

        for key in new_data:
            self.assertEqual(getattr(self.user, key), new_data[key])

    def test_required_fields(self):
        form = self.form(instance=self.user, data={})
        self.assertFalse(form.is_valid())

        required_message = "This field is required."

        self.assertEqual(form.errors["username"][0], required_message)
        self.assertEqual(form.errors["name"][0], required_message)
        self.assertEqual(form.errors["email"][0], required_message)

    def test_email_format(self):
        new_data = {"email": "wrong_format"}

        form = self.form(instance=self.user, data=new_data)
        self.assertFalse(form.is_valid())

        self.assertEqual(form.errors["email"][0], "Enter a valid email address.")

    def test_setting_wants_to_receive_webpush_notifications_to_false_deleted_any_webpush_infos(self):
        self.user.wants_to_receive_webpush_notifications = True
        self.user.save()
        WebpushInformation.objects.create(
            user=self.user,
            browser="a_browser",
            endpoint="http://an-endpoint.local",
            auth="auth_string",
            p256dh="p256dh_string",
        )

        self.assertTrue(WebpushInformation.objects.filter(user=self.user).exists())

        new_data = {
            "username": self.user.username,
            "name": self.user.name,
            "email": self.user.email,
            "wants_to_receive_webpush_notifications": False,
        }

        form = self.form(instance=self.user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()

        self.assertFalse(self.user.wants_to_receive_webpush_notifications)
        self.assertFalse(WebpushInformation.objects.filter(user=self.user).exists())
