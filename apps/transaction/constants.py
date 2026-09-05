from decimal import Decimal

TRANSACTION_FEED_PAGE_SIZE = 10

# Slices below this share of a currency's total are too thin to tap on a phone, so the donut
# collapses them into a single bucket instead of rendering unhittable slivers.
CHART_SMALL_SLICE_SHARE_THRESHOLD = Decimal("0.02")
CHART_SMALL_SLICE_MINIMUM_BUCKET_SIZE = 2
CHART_SMALL_SLICE_BUCKET_COLOR = "#adb5bd"
