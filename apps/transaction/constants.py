from decimal import Decimal

TRANSACTION_FEED_PAGE_SIZE = 10

# Slices below this share of a currency's total are too thin to tap on a phone, so the donut
# collapses them into a single bucket instead of rendering unhittable slivers.
CHART_SMALL_SLICE_SHARE_THRESHOLD = Decimal("0.02")
CHART_SMALL_SLICE_MINIMUM_BUCKET_SIZE = 2
# Deliberately none of the seeded category colors: the bucket is not a category, and a category
# may carry any color a room picks, so the chart also hatches this fill instead of relying on it
# alone to set the bucket apart.
CHART_SMALL_SLICE_BUCKET_COLOR = "#495057"
