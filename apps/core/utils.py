def determine_upload_to(instance, filename: str):
    if instance.UPLOAD_FOLDER_NAME is None:
        return f"{instance._meta.app_label}/{instance._meta.model_name}/{filename}"
    return f"{instance._meta.app_label}/{instance._meta.model_name}/{instance.UPLOAD_FOLDER_NAME}/{filename}"
