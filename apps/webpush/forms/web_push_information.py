from django import forms

from apps.webpush.models.web_push_information import WebpushInformation


class WebPushInformationForm(forms.ModelForm):
    status_type = forms.ChoiceField(choices=[("subscribe", "subscribe"), ("unsubscribe", "unsubscribe")])

    class Meta:
        model = WebpushInformation
        fields = ("user", "browser", "user_agent", "endpoint", "auth", "p256dh", "status_type")

    def save_or_delete(self) -> None:
        data = self.cleaned_data
        user = data["user"]

        if data["status_type"] == "unsubscribe":
            WebpushInformation.objects.filter(user=user, endpoint=data["endpoint"]).delete()
            return

        # An endpoint identifies one browser profile; it may belong to one account only, and rotated keys or a changed
        # user agent must replace the old row instead of adding a duplicate push target.
        WebpushInformation.objects.filter(endpoint=data["endpoint"]).delete()

        if user.wants_to_receive_webpush_notifications:
            WebpushInformation.objects.create(
                user=user,
                browser=data["browser"],
                user_agent=data["user_agent"],
                endpoint=data["endpoint"],
                auth=data["auth"],
                p256dh=data["p256dh"],
            )
