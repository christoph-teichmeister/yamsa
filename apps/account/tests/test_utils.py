from io import BytesIO

from PIL import Image


def build_image_bytes(width: int = 100, height: int = 100) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
