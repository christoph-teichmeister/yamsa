class DummyMeta:
    def __init__(self, app_label: str, model_name: str) -> None:
        self.app_label = app_label
        self.model_name = model_name
