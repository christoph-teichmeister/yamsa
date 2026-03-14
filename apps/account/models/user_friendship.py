from ambient_toolbox.models import CommonInfo
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserFriendship(CommonInfo):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="friendships")
    friend = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="friended_by")

    class Meta:
        verbose_name = _("User friendship")
        verbose_name_plural = _("User friendships")
        constraints = [
            models.UniqueConstraint(fields=["user", "friend"], name="unique_user_friendship"),
            models.CheckConstraint(
                condition=~models.Q(user_id=models.F("friend_id")),
                name="user_cannot_friend_self",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "friend"], name="acc_usrfrndshp_usr_frnd_idx"),
            models.Index(fields=["friend", "user"], name="acc_usrfrndshp_frnd_usr_idx"),
        ]

    def __str__(self):
        return f"{self.user} ↔ {self.friend}"

    def clean(self):
        super().clean()
        if self.user_id is None or self.friend_id is None:
            return
        if self.user_id == self.friend_id:
            error_msg = _("Users cannot be friends with themselves.")
            raise ValidationError(error_msg)
