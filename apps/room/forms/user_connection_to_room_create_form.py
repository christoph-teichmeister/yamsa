from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User
from apps.room.models import Room, UserConnectionToRoom


class UserConnectionToRoomCreateForm(forms.ModelForm):
    email = forms.EmailField()
    room_slug = forms.CharField()

    class ExceptionMessage:
        EMAIL_UNKNOWN = "Email does not exist"
        ROOM_UNKNOWN = "Room does not exist"
        EMAIL_ALREADY_IN_ROOM = "User with this email address is already in this room"

    class Meta:
        model = UserConnectionToRoom
        fields = ("email", "room_slug")

    def clean_email(self) -> str:
        if not User.objects.filter(email=self.cleaned_data["email"]).exists():
            raise ValidationError(self.ExceptionMessage.EMAIL_UNKNOWN)

        return self.cleaned_data["email"]

    def clean_room_slug(self) -> str:
        room_slug = self.cleaned_data["room_slug"]
        try:
            room_exists = Room.objects.filter(slug=room_slug).exists()
        except ValidationError:
            room_exists = False
        if not room_exists:
            raise ValidationError(self.ExceptionMessage.ROOM_UNKNOWN)

        return room_slug

    def clean(self) -> dict:
        cleaned_data = super().clean()
        email, room_slug = cleaned_data.get("email"), cleaned_data.get("room_slug")
        if (
            email
            and room_slug
            and UserConnectionToRoom.objects.filter(user__email=email, room__slug=room_slug).exists()
        ):
            raise ValidationError({"email": self.ExceptionMessage.EMAIL_ALREADY_IN_ROOM})

        return cleaned_data

    def _post_clean(self) -> None:
        if len(self.errors) == 0:
            self.instance.user = User.objects.get(email=self.cleaned_data["email"])
            self.instance.room = Room.objects.get(slug=self.cleaned_data["room_slug"])

        super()._post_clean()
