from django.db import models


class ConsumedImportToken(models.Model):
    """One row per confirmed import token.

    The session payload alone cannot stop two concurrent confirm POSTs: both read it before either
    writes. The cache is no lock either, since CACHES defaults to per-process locmem. The unique
    index is enforced by the database across all workers, and the row is inserted inside the import's
    atomic block, so a failed import rolls it back and a retry can confirm again.
    """

    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.token
