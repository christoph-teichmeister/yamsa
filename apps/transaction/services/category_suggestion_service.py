import unicodedata
from collections import Counter, defaultdict

from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService

# Keywords are matched against the transaction description, so they carry both the German and
# the English wording plus the retailer names the team actually types. A keyword must appear
# under exactly one slug — an ambiguous term ("ticket", "gas", "geschenk") suggests the wrong
# category as often as the right one and is left out on purpose.
BASE_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "accommodation": (
        "airbnb",
        "apartment",
        "camping",
        "ferienwohnung",
        "hostel",
        "hotel",
        "miete",
        "pension",
        "rent",
        "unterkunft",
    ),
    "groceries": (
        "aldi",
        "billa",
        "edeka",
        "einkauf",
        "grocery",
        "groceries",
        "hofer",
        "lebensmittel",
        "lidl",
        "penny",
        "rewe",
        "spar",
        "supermarket",
        "supermarkt",
    ),
    "restaurants-and-bars": (
        "abendessen",
        "bar",
        "beer",
        "bier",
        "brunch",
        "burger",
        "cafe",
        "cocktail",
        "coffee",
        "dinner",
        "essen",
        "fruehstueck",
        "imbiss",
        "kaffee",
        "kneipe",
        "lunch",
        "mittagessen",
        "pizza",
        "pub",
        "restaurant",
        "sushi",
        "wein",
        "wine",
    ),
    "transport": (
        "benzin",
        "bolt",
        "bus",
        "diesel",
        "flight",
        "flug",
        "fuel",
        "maut",
        "oebb",
        "parken",
        "parking",
        "sbb",
        "sprit",
        "tanken",
        "tankstelle",
        "taxi",
        "train",
        "uber",
        "zug",
    ),
    "activities": (
        "ausflug",
        "cinema",
        "concert",
        "eintritt",
        "festival",
        "kino",
        "konzert",
        "museum",
        "skipass",
        "therme",
        "tour",
        "wandern",
        "zoo",
    ),
    "household": (
        "handwerker",
        "haushalt",
        "internet",
        "muell",
        "putzmittel",
        "reinigung",
        "reparatur",
        "strom",
        "waschmittel",
        "wifi",
    ),
    "shopping": (
        "amazon",
        "bekleidung",
        "clothes",
        "drogerie",
        "elektronik",
        "electronics",
        "kleidung",
        "rossmann",
        "schuhe",
        "shopping",
    ),
    "health": (
        "apotheke",
        "arzt",
        "doctor",
        "krankenhaus",
        "medicine",
        "medikament",
        "pharmacy",
        "sonnencreme",
        "zahnarzt",
    ),
    "celebrations": (
        "birthday",
        "christmas",
        "feier",
        "geburtstag",
        "geschenk",
        "gift",
        "hochzeit",
        "party",
        "silvester",
        "weihnachten",
        "wedding",
    ),
}

# The description of a transaction is capped at 50 characters, so a few hundred rows already
# cover the vocabulary a room uses without turning the form into a reporting query.
HISTORY_SAMPLE_SIZE = 500
MINIMUM_KEYWORD_LENGTH = 3


def normalize_keyword(value: str) -> str:
    """
    Fold a word into the form both this service and the client-side matcher compare on.

    The JavaScript counterpart in static/js/category-suggestion.js applies the same NFKD
    fold, so a keyword built here matches what the browser derives from the description.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(character for character in decomposed if not unicodedata.combining(character))
    return without_marks.casefold()


def tokenize(value: str) -> list[str]:
    normalized = normalize_keyword(value)
    tokens = []
    current = []
    for character in normalized:
        if character.isalnum():
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return [token for token in tokens if len(token) >= MINIMUM_KEYWORD_LENGTH and not token.isdigit()]


class CategorySuggestionService:
    """
    Builds the keyword index the transaction form uses to propose a category while typing.

    The index maps a normalized keyword to the id of a category the room actually offers. It
    combines a static vocabulary with what the room did before; the room's own history wins,
    because a room that files "Pizza" under a self-made category means it.
    """

    room: Room

    def __init__(self, room: Room):
        self.room = room

    def build_index(self) -> dict[str, int]:
        categories_by_slug = {
            category.slug: category.id for category in RoomCategoryService(room=self.room).get_category_queryset()
        }
        if not categories_by_slug:
            return {}

        index = self._build_static_index(categories_by_slug)
        index.update(self._build_history_index(set(categories_by_slug.values())))
        return index

    def _build_static_index(self, categories_by_slug: dict[str, int]) -> dict[str, int]:
        index = {}
        for slug, keywords in BASE_CATEGORY_KEYWORDS.items():
            category_id = categories_by_slug.get(slug)
            if category_id is None:
                continue
            for keyword in keywords:
                index[normalize_keyword(keyword)] = category_id
        return index

    def _build_history_index(self, available_category_ids: set[int]) -> dict[str, int]:
        rows = (
            ParentTransaction.objects.filter(room=self.room)
            .order_by("-paid_at", "-id")
            .values_list("description", "category_id")[:HISTORY_SAMPLE_SIZE]
        )

        counts_per_keyword: dict[str, Counter] = defaultdict(Counter)
        for description, category_id in rows:
            if category_id not in available_category_ids:
                continue
            for token in tokenize(description or ""):
                counts_per_keyword[token][category_id] += 1

        # A keyword the room used for two different categories in equal measure says nothing, so
        # only a clear winner makes it into the index.
        index = {}
        for keyword, counts in counts_per_keyword.items():
            ranked = counts.most_common(2)
            if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
                continue
            index[keyword] = ranked[0][0]
        return index
