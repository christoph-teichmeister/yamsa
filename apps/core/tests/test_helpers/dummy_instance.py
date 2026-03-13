from apps.core.tests.test_helpers.dummy_meta import DummyMeta


class DummyInstance:
    def __init__(self, app_label: str, model_name: str, upload_folder_name: str | None) -> None:
        self._meta = DummyMeta(app_label, model_name)
        self.UPLOAD_FOLDER_NAME = upload_folder_name
