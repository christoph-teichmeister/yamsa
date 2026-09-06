"""Form around the profile picture, which is uploaded on its own rather than with the profile."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

from apps.account.models import User
from apps.core.services import CompressPictureService
from apps.core.services.compress_picture_service import MAX_PROFILE_PICTURE_FILE_SIZE

PROFILE_PICTURE_INVALID_IMAGE_ERROR = _("We could not read that file. Please upload a valid image.")
PROFILE_PICTURE_TOO_LARGE_ERROR = _("The profile picture could not be reduced enough. Try a smaller file.")


class ProfilePictureForm(ModelForm):
    """Validate and compress an uploaded avatar."""

    class Meta:
        model = User
        fields = ("profile_picture",)

    def _uploaded_picture(self):
        """The file of this request, if any.

        Without a new upload, `cleaned_data` falls back to the picture already stored — truthy, and
        therefore easy to mistake for an upload. Validating and compressing that one again would
        re-encode a picture that is already compressed and store it under a fresh name, leaving the
        previous file behind as garbage.
        """

        return self.files.get("profile_picture")

    def clean_profile_picture(self):
        """Ensure the uploaded file is a valid image before accepting it."""
        picture = self.cleaned_data.get("profile_picture")
        if not self._uploaded_picture():
            return picture

        try:
            with Image.open(picture) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError(PROFILE_PICTURE_INVALID_IMAGE_ERROR) from exc

        picture.seek(0)
        try:
            compressed_picture = CompressPictureService(picture).process()
        except Exception as exc:
            raise ValidationError(PROFILE_PICTURE_INVALID_IMAGE_ERROR) from exc

        if compressed_picture.size > MAX_PROFILE_PICTURE_FILE_SIZE:
            raise ValidationError(PROFILE_PICTURE_TOO_LARGE_ERROR)

        self._compressed_profile_picture = compressed_picture
        return compressed_picture

    def save(self, commit=True):
        """Persist the compressed picture produced while cleaning."""

        picture = self.cleaned_data.get("profile_picture")
        if picture and self._uploaded_picture():
            compressed_picture = getattr(self, "_compressed_profile_picture", None)
            if compressed_picture is None or compressed_picture is not picture:
                compressed_picture = CompressPictureService(picture).process()
            self.instance.profile_picture = compressed_picture

        return super().save(commit)
