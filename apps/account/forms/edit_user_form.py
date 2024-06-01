from django.forms import ModelForm

from apps.account.models import User


class EditUserForm(ModelForm):
    class Meta:
        model = User
        fields = ("name", "email", "paypal_me_username", "wants_to_receive_webpush_notifications", "profile_picture")
        labels = {
            "wants_to_receive_webpush_notifications": "Receive push notifications",
        }

    def save(self, commit=True):
        # If user opted out of notifications, delete any webpush_infos we have on them
        if self.cleaned_data["wants_to_receive_webpush_notifications"] is False:
            self.instance.webpush_infos.all().delete()

        return super().save(commit)
