import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.transaction.forms.room_category_forms import RoomCategoryCreateForm, RoomCategoryUpdateForm
from apps.transaction.services.room_category_service import RoomCategoryService

logger = logging.getLogger(__name__)


class RoomCategoryManagerView(RoomBaseContext, generic.DetailView):
    model = Room
    slug_url_kwarg = "room_slug"
    template_name = "transaction/category_manager.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._ensure_room_member()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            self._build_context(
                category_creation_form=kwargs.get("category_creation_form"),
                category_update_form=kwargs.get("category_update_form"),
                failed_room_category_id=kwargs.get("failed_room_category_id"),
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        service = self._get_service()

        if action == "create":
            form = RoomCategoryCreateForm(request.POST)
            if form.is_valid():
                self._handle_create(service, form.cleaned_data)
                return self._return_after_action()
            if request.headers.get("HX-Request") == "true":
                list_fragment = self._render_category_list_fragment()
                creation_form_fragment = self._render_category_creation_form_fragment(form, is_oob=True)
                return HttpResponse(list_fragment + creation_form_fragment)
            return self.render_to_response(self._build_context(category_creation_form=form))

        if action == "update":
            form = RoomCategoryUpdateForm(request.POST)
            if form.is_valid():
                self._handle_update(service, form.cleaned_data)
                return self._return_after_action()
            failed_room_category_id = form.data.get("room_category_id")
            logger.warning(
                "RoomCategoryUpdateForm invalid for room %s: %s",
                self.object.pk,
                form.errors.as_json(),
            )
            self.request.toast_queue.error(_("Unable to update that category. Please correct the highlighted fields."))
            if request.headers.get("HX-Request") == "true":
                return self._render_category_list(update_form=form, failed_room_category_id=failed_room_category_id)
            return self.render_to_response(
                self._build_context(
                    category_creation_form=RoomCategoryCreateForm(),
                    category_update_form=form,
                    failed_room_category_id=failed_room_category_id,
                )
            )

        if action == "delete":
            room_category_id = request.POST.get("room_category_id")
            if room_category_id:
                deleted_category = service.delete_room_category(int(room_category_id))
                if deleted_category:
                    self.request.toast_queue.success(self._get_category_deletion_success_message(deleted_category.name))
            return self._return_after_action()

        return self.get(request, *args, **kwargs)

    def _return_after_action(self):
        if self.request.headers.get("HX-Request") == "true":
            list_fragment = self._render_category_list_fragment()
            creation_form_fragment = self._render_category_creation_form_fragment(RoomCategoryCreateForm(), is_oob=True)
            return HttpResponse(list_fragment + creation_form_fragment)
        return redirect(self.request.path)

    def _render_category_list(self, update_form=None, failed_room_category_id=None):
        return HttpResponse(self._render_category_list_fragment(update_form, failed_room_category_id))

    def _render_category_list_fragment(self, update_form=None, failed_room_category_id=None):
        service = self._get_service()
        return render_to_string(
            "transaction/partials/_room_category_list.html",
            {
                "room_categories": service.get_categories(),
                "room_category_update_form": update_form,
                "failed_room_category_id": failed_room_category_id,
            },
            request=self.request,
        )

    def _render_category_creation_form_fragment(self, form, *, is_oob=False, success_message=None):
        if success_message is None:
            success_message = self._get_category_creation_success_message()
        return render_to_string(
            "transaction/partials/_room_category_creation_form.html",
            {
                "category_creation_form": form,
                "category_creation_success_message": success_message,
                "is_oob": is_oob,
            },
            request=self.request,
        )

    def _build_context(self, *, category_creation_form=None, category_update_form=None, failed_room_category_id=None):
        service = self._get_service()
        return {
            "category_creation_form": category_creation_form or RoomCategoryCreateForm(),
            "room_categories": service.get_categories(),
            "category_creation_success_message": self._get_category_creation_success_message(),
            "room_category_update_form": category_update_form,
            "failed_room_category_id": failed_room_category_id,
        }

    def _handle_create(self, service: RoomCategoryService, cleaned_data: dict):
        order_index = cleaned_data.get("order_index")
        if order_index is None:
            order_index = service.get_next_order_index()
        service.create_room_category(
            name=cleaned_data["name"],
            emoji=cleaned_data["emoji"],
            color=cleaned_data.get("color") or None,
            order_index=order_index,
            make_default=cleaned_data.get("make_default", False),
        )
        self.request.toast_queue.success(self._get_category_creation_success_message())

    def _handle_update(self, service: RoomCategoryService, cleaned_data: dict):
        service.update_room_category(
            room_category_id=cleaned_data["room_category_id"],
            order_index=cleaned_data["order_index"],
            make_default=cleaned_data.get("make_default", False),
        )

    def _get_service(self) -> RoomCategoryService:
        return RoomCategoryService(room=self.object)

    def _ensure_room_member(self) -> None:
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied
        if user == self.object.created_by or user.is_superuser:
            return
        if not self.object.users.filter(pk=user.pk).exists():
            raise PermissionDenied

    def _get_category_creation_success_message(self) -> str:
        return str(_("Category added."))

    def _get_category_deletion_success_message(self, category_name: str) -> str:
        return str(_('Category "%(category)s" deleted.') % {"category": category_name})
