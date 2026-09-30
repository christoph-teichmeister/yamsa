class FullCleanOnSaveMixin:
    def save(self, *args: object, **kwargs: object):
        self.full_clean()
        super().save(*args, **kwargs)
