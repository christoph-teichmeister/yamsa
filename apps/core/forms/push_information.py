from django import forms

from apps.core.models.push_information import PushInformation


class PushInformationForm(forms.Form):
    status_type = forms.ChoiceField(choices=[("subscribe", "subscribe"), ("unsubscribe", "unsubscribe")])

    def save_or_delete(self, user, status_type):
        # Ensure get_or_create matches exactly
        data = {"user": None}

        if user.is_authenticated:
            data["user"] = user

        push_info, created = PushInformation.objects.get_or_create(**data)

        # If unsubscribe is called, that means need to delete the browser
        # and notification info from server.
        if status_type == "unsubscribe":
            push_info.delete()
