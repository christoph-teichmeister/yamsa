from django.db import models
from django.db.models import BooleanField, Exists, ExpressionWrapper, Max, OuterRef
from django.db.models.functions import Substr, Upper


class RoomQuerySet(models.QuerySet):
    def visible_for(self, user):
        if user.is_anonymous:
            return self.none()

        if user.is_superuser:
            return self.all()

        return self.filter(users=user)

    def annotate_user_is_in_room_for_user_id(self, user_id: int):
        from apps.account.models import User

        return self.annotate(
            user_is_in_room=ExpressionWrapper(
                Exists(User.objects.filter(id=user_id, rooms=OuterRef("id"))),
                output_field=BooleanField(),
            ),
        )

    def annotate_last_transaction_lastmodified_at_date(self):
        return self.annotate(last_transaction_created_at_date=Max("parent_transactions__lastmodified_at"))

    def annotate_capitalised_initials(self):
        return self.annotate(capitalised_initials=Upper(Substr("name", 1, 2)))
