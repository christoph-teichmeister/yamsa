from django import forms
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.currency.models import Currency
from apps.importer.dataclasses import CategoryAssignment, ParsedImport, PersonAssignment
from apps.importer.services.person_candidate_service import PersonCandidateService
from apps.room.models import Room
from apps.transaction.forms.room_category_forms.validators import validate_single_emoji
from apps.transaction.models import BASE_CATEGORY_SLUGS, Category

PERSON_FIELD_PREFIX = "person_"
CATEGORY_FIELD_PREFIX = "category_"

ROOM_NAME_MAX_LENGTH = Room._meta.get_field("name").max_length
ROOM_DESCRIPTION_MAX_LENGTH = Room._meta.get_field("description").max_length
GUEST_NAME_MAX_LENGTH = User._meta.get_field("name").max_length
CATEGORY_NAME_MAX_LENGTH = Category._meta.get_field("name").max_length
CATEGORY_EMOJI_MAX_LENGTH = Category._meta.get_field("emoji").max_length


class ImportPreviewForm(forms.Form):
    """
    Maps every person column and every source category of a parsed file, and carries the
    fields for the room that the import creates.
    """

    room_name = forms.CharField(max_length=ROOM_NAME_MAX_LENGTH, label=_("Room name"))
    room_description = forms.CharField(max_length=ROOM_DESCRIPTION_MAX_LENGTH, label=_("Description"))
    preferred_currency = forms.ModelChoiceField(queryset=Currency.objects.all(), label=_("Currency"))

    def __init__(self, *args, parsed: ParsedImport, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.parsed = parsed
        self.user = user

        candidate_service = PersonCandidateService(user=user)
        self.candidates = candidate_service.get_candidates()
        self.base_categories = list(Category.objects.filter(slug__in=BASE_CATEGORY_SLUGS).order_by("order_index", "id"))

        self._build_person_fields(candidate_service)
        self._build_category_fields()

    def _build_person_fields(self, candidate_service: PersonCandidateService) -> None:
        person_choices = [
            (PersonAssignment.ME, _("That is me")),
            *[(f"user-{candidate.pk}", candidate.name) for candidate in self.candidates],
            (PersonAssignment.GUEST, _("New guest")),
        ]

        for index, person in enumerate(self.parsed.people):
            match = candidate_service.match_by_name(person, candidates=self.candidates)
            self.fields[f"{PERSON_FIELD_PREFIX}{index}"] = forms.ChoiceField(
                choices=person_choices,
                label=person,
                # A name that already exists is preselected — only offering the option would
                # still let people click "new guest" and create the duplicate.
                initial=f"user-{match.pk}" if match else PersonAssignment.GUEST,
            )
            self.fields[f"{PERSON_FIELD_PREFIX}{index}_name"] = forms.CharField(
                max_length=GUEST_NAME_MAX_LENGTH, required=False, initial=person, label=_("Guest name")
            )

    def _build_category_fields(self) -> None:
        category_choices = [(category.slug, f"{category.emoji} {category.name}") for category in self.base_categories]
        category_choices.append((CategoryAssignment.NEW, _("Create as a new room category")))

        for index, category in enumerate(self.parsed.categories):
            self.fields[f"{CATEGORY_FIELD_PREFIX}{index}"] = forms.ChoiceField(
                choices=category_choices,
                label=category.label,
                initial=category.suggested_slug,
            )
            self.fields[f"{CATEGORY_FIELD_PREFIX}{index}_name"] = forms.CharField(
                max_length=CATEGORY_NAME_MAX_LENGTH, required=False, initial=category.label, label=_("Category name")
            )
            self.fields[f"{CATEGORY_FIELD_PREFIX}{index}_emoji"] = forms.CharField(
                max_length=CATEGORY_EMOJI_MAX_LENGTH, required=False, initial=category.suggested_emoji, label=_("Emoji")
            )

    def person_rows(self):
        for index, person in enumerate(self.parsed.people):
            yield person, self[f"{PERSON_FIELD_PREFIX}{index}"], self[f"{PERSON_FIELD_PREFIX}{index}_name"]

    def category_rows(self):
        for index, category in enumerate(self.parsed.categories):
            yield (
                category,
                self[f"{CATEGORY_FIELD_PREFIX}{index}"],
                self[f"{CATEGORY_FIELD_PREFIX}{index}_name"],
                self[f"{CATEGORY_FIELD_PREFIX}{index}_emoji"],
            )

    def clean(self):
        cleaned_data = super().clean()
        self._clean_people(cleaned_data)
        self._clean_categories(cleaned_data)
        return cleaned_data

    def _clean_people(self, cleaned_data: dict) -> None:
        assignments: list[PersonAssignment] = []
        me_count = 0
        seen_user_ids: set[int] = set()
        seen_guest_names: set[str] = set()

        for index, person in enumerate(self.parsed.people):
            field_name = f"{PERSON_FIELD_PREFIX}{index}"
            choice = cleaned_data.get(field_name)
            if not choice:
                continue

            if choice == PersonAssignment.ME:
                me_count += 1
                assignments.append(PersonAssignment(column=person, kind=PersonAssignment.ME))
                continue

            if choice == PersonAssignment.GUEST:
                # The fallback is the file's column heading, which carries no length bound of its own.
                guest_name = (cleaned_data.get(f"{field_name}_name") or person).strip()[:GUEST_NAME_MAX_LENGTH]
                if not guest_name:
                    self.add_error(f"{field_name}_name", _("Please provide a name for this guest."))
                    continue
                if guest_name.casefold() in seen_guest_names:
                    self.add_error(f"{field_name}_name", _("This guest name is already used for another column."))
                    continue
                seen_guest_names.add(guest_name.casefold())
                assignments.append(PersonAssignment(column=person, kind=PersonAssignment.GUEST, guest_name=guest_name))
                continue

            # Safe without a further check: ChoiceField.validate() already rejected anything the
            # candidate list did not produce, so an arbitrary pk cannot reach this line.
            user_id = int(choice.removeprefix("user-"))
            if user_id in seen_user_ids:
                self.add_error(field_name, _("This person is already assigned to another column."))
                continue
            seen_user_ids.add(user_id)
            assignments.append(PersonAssignment(column=person, kind=PersonAssignment.EXISTING, user_id=user_id))

        if me_count != 1:
            raise forms.ValidationError(_("Mark exactly one column as 'That is me'."))

        cleaned_data["person_assignments"] = assignments

    def _clean_categories(self, cleaned_data: dict) -> None:
        assignments: list[CategoryAssignment] = []

        for index, category in enumerate(self.parsed.categories):
            field_name = f"{CATEGORY_FIELD_PREFIX}{index}"
            choice = cleaned_data.get(field_name)
            if not choice:
                continue

            if choice != CategoryAssignment.NEW:
                assignments.append(
                    CategoryAssignment(label=category.label, kind=CategoryAssignment.EXISTING, slug=choice)
                )
                continue

            # Same as for guests: the fallback is unbounded source data.
            name = (cleaned_data.get(f"{field_name}_name") or category.label).strip()[:CATEGORY_NAME_MAX_LENGTH]
            emoji = (cleaned_data.get(f"{field_name}_emoji") or "").strip()
            if not name:
                self.add_error(f"{field_name}_name", _("Please provide a name for this category."))
                continue
            try:
                validate_single_emoji(emoji)
            except forms.ValidationError as error:
                self.add_error(f"{field_name}_emoji", error)
                continue

            assignments.append(
                CategoryAssignment(label=category.label, kind=CategoryAssignment.NEW, name=name, emoji=emoji)
            )

        cleaned_data["category_assignments"] = assignments
