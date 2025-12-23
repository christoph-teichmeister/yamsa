from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.transaction.forms.room_category_forms import RoomCategoryCreateForm, RoomCategoryUpdateForm
from apps.transaction.services.room_category_service import RoomCategoryService


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
        context.update(self._build_context(category_creation_form=kwargs.get("category_creation_form")))
        return context

    def post(self, request, *args, **kwargs):
        if not getattr(self, "object", None):
            self.object = self.get_object()
        self._ensure_room_member()
        action = request.POST.get("action")
        service = self._get_service()

        if action == "create":
            form = RoomCategoryCreateForm(request.POST)
            if form.is_valid():
                self._handle_create(service, form.cleaned_data)
                return self._return_after_action()
            return self.render_to_response(self._build_context(category_creation_form=form))

        if action == "update":
            form = RoomCategoryUpdateForm(request.POST)
            if form.is_valid():
                self._handle_update(service, form.cleaned_data)
                return self._return_after_action()
            return self._return_after_action()

        if action == "delete":
            room_category_id = request.POST.get("room_category_id")
            if room_category_id:
                service.delete_room_category(int(room_category_id))
            return self._return_after_action()

        return self.get(request, *args, **kwargs)

    def _return_after_action(self):
        if self.request.headers.get("HX-Request") == "true":
            return self._render_category_list()
        return redirect(self.request.path)

    def _render_category_list(self):
        service = self._get_service()
        return render(
            self.request,
            "transaction/partials/_room_category_list.html",
            {"room_categories": service.get_categories()},
        )

    def _build_context(self, *, category_creation_form=None):
        service = self._get_service()
        return {
            "category_creation_form": category_creation_form or RoomCategoryCreateForm(),
            "room_categories": service.get_categories(),
            "category_creation_success_message": self._get_category_creation_success_message(),
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
        if not getattr(self, "object", None):
            self.object = self.get_object()
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
