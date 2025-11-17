import uuid


def determine_upload_to(instance, filename: str):
    """Return an upload path that keeps the folder structure but guarantees a unique filename."""
    base_path = f"{instance._meta.app_label}/{instance._meta.model_name}"
    if instance.UPLOAD_FOLDER_NAME is not None:
        base_path = f"{base_path}/{instance.UPLOAD_FOLDER_NAME}"
    unique_filename = f"{uuid.uuid4()}-{filename}"
    return f"{base_path}/{unique_filename}"
