class FullCleanOnSaveMixin:
    def save(self, *args: object, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
