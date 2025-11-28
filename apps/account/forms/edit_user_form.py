from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from apps.account.models import User

MAX_PROFILE_PICTURE_FILE_SIZE = 3 * 1024 * 1024  # 3 MB
MAX_PROFILE_PICTURE_DIMENSION = 2048
PROFILE_PICTURE_SIZE_ERROR = "Please upload an image smaller than 3 MB."
PROFILE_PICTURE_DIMENSION_ERROR = "Please upload an image with dimensions up to 2048x2048 pixels."
PROFILE_PICTURE_INVALID_IMAGE_ERROR = "We could not read that file. Please upload a valid image."


class EditUserForm(ModelForm):
    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "profile_picture",
            "paypal_me_username",
            "language",
            "wants_to_receive_webpush_notifications",
            "wants_to_receive_payment_reminders",
            "wants_to_receive_room_reminders",
        )
        labels = {
            "wants_to_receive_webpush_notifications": _("Receive push notifications"),
            "language": _("Preferred language"),
            "wants_to_receive_payment_reminders": _("Receive payment reminder emails"),
            "wants_to_receive_room_reminders": _("Receive room reminder emails"),
        }

    def save(self, commit=True):
        # If user opted out of notifications, delete any webpush_infos we have on them
        if self.cleaned_data["wants_to_receive_webpush_notifications"] is False:
            self.instance.webpush_infos.all().delete()

        return super().save(commit)

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        if not picture:
            return picture

        if picture.size > MAX_PROFILE_PICTURE_FILE_SIZE:
            raise ValidationError(PROFILE_PICTURE_SIZE_ERROR)

        try:
            width, height = get_image_dimensions(picture)
        except Exception as e:
            raise ValidationError(PROFILE_PICTURE_INVALID_IMAGE_ERROR) from e

        if width > MAX_PROFILE_PICTURE_DIMENSION or height > MAX_PROFILE_PICTURE_DIMENSION:
            raise ValidationError(PROFILE_PICTURE_DIMENSION_ERROR)

        return picture
