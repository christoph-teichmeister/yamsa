from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User
from apps.room.models import Room, UserConnectionToRoom


class UserConnectionToRoomCreateForm(forms.ModelForm):
    email = forms.EmailField()
    room_slug = forms.CharField()

    class Meta:
        model = UserConnectionToRoom
        fields = ("email", "room_slug")

    def clean_email(self):
        if not User.objects.filter(email=self.cleaned_data["email"]).exists():
            raise ValidationError("Email does not exist")

        return self.cleaned_data["email"]

    def clean(self):
        if UserConnectionToRoom.objects.filter(
            user__email=self.data["email"], room__slug=self.data["room_slug"]
        ).exists():
            raise ValidationError({"email": "User with this email address is already in this room"})

    def _post_clean(self):
        self.instance.user = User.objects.get(email=self.cleaned_data["email"])
        self.instance.room = Room.objects.get(slug=self.cleaned_data["room_slug"])

        super()._post_clean()
