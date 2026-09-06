from io import BytesIO

from PIL import Image


def build_image_bytes(width: int = 100, height: int = 100) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def contains_attribute(content: str, name: str, value: str) -> bool:
    """Whether the rendered HTML carries `name="value"`.

    MinifyHtmlMiddleware drops the quotes around values that do not need them, so an assertion on
    the quoted spelling alone passes locally and fails through the middleware.
    """

    return f'{name}="{value}"' in content or f"{name}={value} " in content or f"{name}={value}>" in content
