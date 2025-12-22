import os
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps

MAX_PROFILE_PICTURE_DIMENSION = 2048
MAX_PROFILE_PICTURE_FILE_SIZE = 3 * 1024 * 1024  # 3 MB
PROFILE_PICTURE_DEFAULT_QUALITY = 85
PROFILE_PICTURE_MIN_QUALITY = 50
PROFILE_PICTURE_QUALITY_STEP = 5


class CompressPictureService:
    """Compress an uploaded image so it stays within size limits."""

    MIME_MAP = {"jpg": "image/jpeg", "png": "image/png"}

    def __init__(self, picture, field_name=None, charset=None):
        self.picture = picture
        self.field_name = field_name or getattr(picture, "field_name", "profile_picture")
        self.charset = charset or getattr(picture, "charset", None)

    def process(self):
        """Return a compressed InMemoryUploadedFile built from the original upload."""
        image = ImageOps.exif_transpose(Image.open(self.picture))
        image.thumbnail(
            (MAX_PROFILE_PICTURE_DIMENSION, MAX_PROFILE_PICTURE_DIMENSION),
            Image.LANCZOS,
        )

        target_format = self._determine_format(image)
        save_image = self._prepare_image_for_format(image, target_format)
        quality = PROFILE_PICTURE_DEFAULT_QUALITY
        buffer = self._save_image_to_buffer(save_image, target_format, quality)

        if target_format == "JPEG":
            while buffer.getbuffer().nbytes > MAX_PROFILE_PICTURE_FILE_SIZE and quality > PROFILE_PICTURE_MIN_QUALITY:
                # Shrink the JPEG quality stepwise until the file is small enough.
                quality = max(quality - PROFILE_PICTURE_QUALITY_STEP, PROFILE_PICTURE_MIN_QUALITY)
                buffer = self._save_image_to_buffer(save_image, target_format, quality)

        if target_format == "PNG" and buffer.getbuffer().nbytes > MAX_PROFILE_PICTURE_FILE_SIZE:
            # PNG uploads that are still too bulky are converted to JPEGs.
            target_format = "JPEG"
            save_image = self._prepare_image_for_format(image, target_format)
            quality = PROFILE_PICTURE_MIN_QUALITY
            buffer = self._save_image_to_buffer(save_image, target_format, quality)

        buffer.seek(0)
        file_root, _ = os.path.splitext(self.picture.name)
        extension = {
            "JPEG": "jpg",
            "PNG": "png",
        }.get(target_format, "jpg")
        file_name = f"{file_root}.{extension}"
        content_type = self.MIME_MAP.get(extension, f"image/{extension}")

        # Wrap the buffer so Django views the compressed image as a usable upload.
        return InMemoryUploadedFile(
            buffer,
            self.field_name,
            file_name,
            content_type,
            buffer.getbuffer().nbytes,
            self.charset,
        )

    @staticmethod
    def _save_image_to_buffer(image, target_format, quality):
        """Persist the PIL image to a buffer using the requested format and quality."""
        output = BytesIO()
        save_kwargs = {}
        if target_format == "JPEG":
            save_kwargs.update(
                quality=quality,
                optimize=True,
                progressive=True,
            )
        elif target_format == "PNG":
            save_kwargs["optimize"] = True

        image.save(output, format=target_format, **save_kwargs)
        output.seek(0)
        return output

    @staticmethod
    def _determine_format(image):
        """Prefer PNG when transparency exists, otherwise output JPEG."""
        has_alpha = "A" in image.getbands()
        return "PNG" if has_alpha else "JPEG"

    @staticmethod
    def _prepare_image_for_format(image, target_format):
        """Convert or preserve the image mode depending on the chosen format."""
        if target_format == "JPEG":
            if image.mode not in ("RGB", "L"):
                return image.convert("RGB")
            return image

        if target_format == "PNG":
            if image.mode in ("RGB", "RGBA", "P"):
                return image.convert("RGBA" if "A" in image.getbands() else "RGB")
            return image.convert("RGBA")

        return image
