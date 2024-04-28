from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User
from apps.room.models import Room, UserConnectionToRoom


class UserConnectionToRoomCreateForm(forms.ModelForm):
    email = forms.EmailField()
    room_slug = forms.CharField()

    class ExceptionMessage:
        EMAIL_UNKNOWN = "Email does not exist"
        EMAIL_ALREADY_IN_ROOM = "User with this email address is already in this room"

    class Meta:
        model = UserConnectionToRoom
        fields = ("email", "room_slug")

    def clean_email(self):
        if not User.objects.filter(email=self.cleaned_data["email"]).exists():
            raise ValidationError(self.ExceptionMessage.EMAIL_UNKNOWN)

        return self.cleaned_data["email"]

    def clean(self):
        if UserConnectionToRoom.objects.filter(
            user__email=self.data["email"], room__slug=self.data["room_slug"]
        ).exists():
            raise ValidationError({"email": self.ExceptionMessage.EMAIL_ALREADY_IN_ROOM})

    def _post_clean(self):
        if len(self.errors) == 0:
            self.instance.user = User.objects.get(email=self.cleaned_data["email"])
            self.instance.room = Room.objects.get(slug=self.cleaned_data["room_slug"])

        super()._post_clean()
