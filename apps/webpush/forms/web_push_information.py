from django import forms

from apps.webpush.models.web_push_information import WebpushInformation


class WebPushInformationForm(forms.ModelForm):
    status_type = forms.ChoiceField(choices=[("subscribe", "subscribe"), ("unsubscribe", "unsubscribe")])

    class Meta:
        model = WebpushInformation
        fields = ("user", "browser", "user_agent", "endpoint", "auth", "p256dh", "status_type")

    def save_or_delete(self):
        status_type = self.cleaned_data.pop("status_type")
        defaults = {"browser": self.cleaned_data.pop("browser")}

        push_info, created = WebpushInformation.objects.get_or_create(**self.cleaned_data, defaults=defaults)

        # If unsubscribe is called, that means need to delete the browser and notification info from server.
        if status_type == "unsubscribe":
            push_info.delete()
