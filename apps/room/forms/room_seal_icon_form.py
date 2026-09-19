"""Form around picking a predefined seal icon, on its own rather than with the room's fields."""

from django.forms import ModelForm

from apps.room.models import Room


class RoomSealIconForm(ModelForm):
    """Pick one of the predefined seal icons, replacing any custom image."""

    class Meta:
        model = Room
        fields = ("seal_icon",)

    def save(self, commit=True):
        if self.instance.seal_image:
            self.instance.seal_image.delete(save=False)
        self.instance.seal_image = None
        return super().save(commit)
