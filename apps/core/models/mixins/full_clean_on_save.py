class FullCleanOnSaveMixin:
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
