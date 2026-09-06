from apps.account.forms import EditUserForm
from apps.webpush.models import WebpushInformation


class TestEditUserForm:
    form_class = EditUserForm

    def test_regular(self, user):
        new_data = {
            "name": "new_name",
            "email": "new_email@local.local",
            "paypal_me_username": "new_paypal_me_username",
            "wants_to_receive_webpush_notifications": True,
            "wants_to_receive_payment_reminders": False,
        }

        form = self.form_class(instance=user, data=new_data)
        assert form.is_valid()

        form.save()
        user.refresh_from_db()

        for key, value in new_data.items():
            assert getattr(user, key) == value

    def test_required_fields(self, user):
        form = self.form_class(instance=user, data={})
        assert not form.is_valid()

        required_message = "This field is required."

        assert form.errors["name"][0] == required_message
        assert form.errors["email"][0] == required_message

    def test_email_format(self, user):
        form = self.form_class(instance=user, data={"email": "wrong_format"})
        assert not form.is_valid()

        assert form.errors["email"][0] == "Enter a valid email address."

    def test_setting_wants_to_receive_webpush_notifications_to_false_deleted_any_webpush_infos(self, user):
        user.wants_to_receive_webpush_notifications = True
        user.save()
        WebpushInformation.objects.create(
            user=user,
            browser="a_browser",
            endpoint="http://an-endpoint.local",
            auth="auth_string",
            p256dh="p256dh_string",
        )

        assert WebpushInformation.objects.filter(user=user).exists()

        form = self.form_class(
            instance=user,
            data={
                "name": user.name,
                "email": user.email,
                "wants_to_receive_webpush_notifications": False,
                "wants_to_receive_payment_reminders": True,
            },
        )
        assert form.is_valid()

        form.save()

        assert not user.wants_to_receive_webpush_notifications
        assert not WebpushInformation.objects.filter(user=user).exists()
