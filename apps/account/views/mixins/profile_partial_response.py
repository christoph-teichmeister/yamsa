from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.account.forms import EditUserForm, ProfilePictureForm

PROFILE_SHEET_TEMPLATE = "account/partials/_profile_sheet.html"
PROFILE_PHOTO_TEMPLATE = "account/partials/_profile_photo.html"


class ProfilePartialResponseMixin:
    """Render a single part of the profile page, for the htmx swaps that replace it in place."""

    def is_htmx_request(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def render_profile_sheet(self, user, *, form=None) -> HttpResponse:
        """Answer with just the sheet, so the browser keeps the page it is already on."""

        return HttpResponse(
            render_to_string(
                PROFILE_SHEET_TEMPLATE,
                {
                    "user": user,
                    "form": form if form is not None else EditUserForm(instance=user),
                },
                request=self.request,
            )
        )

    def render_profile_photo(self, user, *, picture_form=None, dialog_is_open: bool = False) -> HttpResponse:
        """Answer with just the photo and its dialog.

        The photo has its own cycle, so swapping only this part leaves the surrounding sheet — and
        with it whether the profile is currently being edited — exactly as the viewer left it.
        """

        return HttpResponse(
            render_to_string(
                PROFILE_PHOTO_TEMPLATE,
                {
                    "user": user,
                    "picture_form": picture_form if picture_form is not None else ProfilePictureForm(instance=user),
                    "photo_dialog_is_open": dialog_is_open,
                },
                request=self.request,
            )
        )
