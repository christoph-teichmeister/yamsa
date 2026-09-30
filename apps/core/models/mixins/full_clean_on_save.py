class FullCleanOnSaveMixin:
    def save(self, *args, **kwargs: object):
        self.full_clean()
        super().save(*args, **kwargs)
