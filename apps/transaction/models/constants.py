DEFAULT_CATEGORY_SLUG = "misc"
BASE_CATEGORY_SLUGS = (
    "accommodation",
    "groceries",
    "restaurants-and-bars",
    "transport",
    "activities",
    "household",
    "shopping",
    "health",
    "celebrations",
    DEFAULT_CATEGORY_SLUG,
)


def resolve_default_category_pk() -> int:
    from apps.transaction.models.category import Category

    category, _ = Category.objects.get_or_create(
        slug=DEFAULT_CATEGORY_SLUG,
        defaults={
            "name": "Miscellaneous",
            "emoji": "🌀",
            "color": "#ADB5BD",
            "order_index": 9,
            "is_default": True,
        },
    )
    return category.pk
