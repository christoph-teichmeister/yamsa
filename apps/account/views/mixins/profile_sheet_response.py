from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.account.forms import EditUserForm

PROFILE_SHEET_TEMPLATE = "account/partials/_profile_sheet.html"


class ProfileSheetResponseMixin:
    """Render the profile sheet on its own, for the htmx swaps that replace it in place."""

    def is_htmx_request(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def render_profile_sheet(self, user, *, is_editing: bool, form=None) -> HttpResponse:
        """Answer with just the sheet, so the browser keeps the page it is already on."""

        return HttpResponse(
            render_to_string(
                PROFILE_SHEET_TEMPLATE,
                {
                    "user": user,
                    "form": form if form is not None else EditUserForm(instance=user),
                    "profile_is_editing": is_editing,
                },
                request=self.request,
            )
        )
