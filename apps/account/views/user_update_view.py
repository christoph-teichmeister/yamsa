import json

from django.contrib.auth import mixins
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.views import generic

from apps.account.constants import LANGUAGE_SESSION_KEY
from apps.account.forms import EditUserForm
from apps.account.models import User
from apps.account.views.mixins.profile_partial_response import ProfilePartialResponseMixin


class UserUpdateView(ProfilePartialResponseMixin, mixins.LoginRequiredMixin, generic.UpdateView):
    # The profile is one page that switches between reading and editing in place, so this view
    # renders the very same template — only with the sheet unlocked.
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User
    form_class = EditUserForm

    def dispatch(self, request, *args, **kwargs):
        # A user may only ever edit their own account — the edit button in the UI is hidden for
        # every other profile, but the URL itself had no server-side check to back that up.
        if request.user.id != kwargs["pk"]:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(viewname="account:detail", kwargs={"pk": self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_is_editing"] = True
        return context

    def form_valid(self, form):
        language_changed = "language" in form.changed_data
        response = super().form_valid(form)
        if self.request.user == self.object:
            language_value = self.object.language
            if language_value:
                translation.activate(language_value)
                self.request.session[LANGUAGE_SESSION_KEY] = language_value
            else:
                self.request.session.pop(LANGUAGE_SESSION_KEY, None)

        if not self.is_htmx_request():
            return response

        if language_changed:
            # Side menu, navigation and toasts sit outside the sheet and are already rendered in
            # the previous language — this is the one save that cannot be a partial swap.
            return HttpResponse(status=204, headers={"HX-Refresh": "true"})

        sheet_response = self.render_profile_sheet(self.object, is_editing=False)
        # The service worker subscribes or unsubscribes off this trigger, which the full page load
        # used to deliver.
        sheet_response["HX-Trigger"] = json.dumps(
            {"notificationsEnabled": self.object.wants_to_receive_webpush_notifications}
        )
        return sheet_response

    def form_invalid(self, form):
        if self.is_htmx_request():
            return self.render_profile_sheet(self.object, is_editing=True, form=form)
        return super().form_invalid(form)
