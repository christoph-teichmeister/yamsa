"""Form around uploading a custom seal image, on its own rather than with the room's fields."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

from apps.core.services import CompressPictureService
from apps.core.services.compress_picture_service import MAX_PROFILE_PICTURE_FILE_SIZE
from apps.room.models import Room

SEAL_IMAGE_INVALID_IMAGE_ERROR = _("We could not read that file. Please upload a valid image.")
SEAL_IMAGE_TOO_LARGE_ERROR = _("The seal image could not be reduced enough. Try a smaller file.")


class RoomSealImageForm(ModelForm):
    """Validate and compress an uploaded seal image, replacing any icon choice."""

    class Meta:
        model = Room
        fields = ("seal_image",)

    def clean_seal_image(self):
        picture = self.cleaned_data.get("seal_image")
        if not self.files.get("seal_image"):
            raise ValidationError(SEAL_IMAGE_INVALID_IMAGE_ERROR)

        try:
            with Image.open(picture) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError(SEAL_IMAGE_INVALID_IMAGE_ERROR) from exc

        picture.seek(0)
        try:
            compressed_picture = CompressPictureService(picture, field_name="seal_image").process()
        except Exception as exc:
            raise ValidationError(SEAL_IMAGE_INVALID_IMAGE_ERROR) from exc

        if compressed_picture.size > MAX_PROFILE_PICTURE_FILE_SIZE:
            raise ValidationError(SEAL_IMAGE_TOO_LARGE_ERROR)

        self._compressed_seal_image = compressed_picture
        return compressed_picture

    def save(self, commit=True):
        """Persist the compressed image produced while cleaning.

        `construct_instance()` already set `self.instance.seal_image` to this same compressed
        file during validation - deleting "the old one" here would delete and close the file
        about to be saved, not whatever was stored before it. A previous upload is left behind
        as orphaned storage, same as ProfilePictureForm does for a user's old avatar.
        """
        compressed_picture = getattr(self, "_compressed_seal_image", None)
        if compressed_picture is not None:
            self.instance.seal_image = compressed_picture
        self.instance.seal_icon = ""
        return super().save(commit)
