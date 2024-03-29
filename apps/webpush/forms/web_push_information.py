from django import forms

from apps.webpush.models.web_push_information import WebpushInformation


class WebPushInformationForm(forms.ModelForm):
    status_type = forms.ChoiceField(choices=[("subscribe", "subscribe"), ("unsubscribe", "unsubscribe")])

    class Meta:
        model = WebpushInformation
        fields = ("user", "browser", "user_agent", "endpoint", "auth", "p256dh", "status_type")

    def save_or_delete(self):
        status_type = self.cleaned_data.pop("status_type")  # pop status_type from cleaned_data, so get_or_create works
        defaults = {"browser": self.cleaned_data.pop("browser")}

        push_info, created = WebpushInformation.objects.get_or_create(**self.cleaned_data, defaults=defaults)

        # If unsubscribe is passed, delete the browser and notification info
        if status_type == "unsubscribe" or not self.cleaned_data.get("user").wants_to_receive_webpush_notifications:
            push_info.delete()
