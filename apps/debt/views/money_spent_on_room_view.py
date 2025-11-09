from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone
from django.views import generic
from django_context_decorator import context

from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.transaction.models import ChildTransaction


class RoomChildTransactionQuerysetMixin:
    def get_base_queryset(self):
        return ChildTransaction.objects.filter(parent_transaction__room=self.request.room)


class MoneySpentOnRoomView(RoomChildTransactionQuerysetMixin, DebtBaseContext, generic.TemplateView):
    template_name = "transaction/partials/_money_spent_on_room.html"

    @context
    @property
    def money_spent_per_person_qs(self):
        return (
            self.get_base_queryset()
            .values("parent_transaction__paid_by__name", "parent_transaction__currency__sign")
            .annotate(
                paid_by_name=F("parent_transaction__paid_by__name"),
                currency_sign=F("parent_transaction__currency__sign"),
                total_spent_per_person=Sum("value"),
            )
            .order_by("parent_transaction__paid_by__name")
        )

    @context
    @property
    def total_money_spent(self):
        return (
            self.get_base_queryset()
            .values("parent_transaction__currency__sign")
            .annotate(currency_sign=F("parent_transaction__currency__sign"), total_spent=Sum("value"))
        )

    @context
    @property
    def money_owed_per_person_qs(self):
        return (
            self.get_base_queryset()
            .values("paid_for__name", "parent_transaction__currency__sign")
            .annotate(currency_sign=F("parent_transaction__currency__sign"), total_owed_per_person=Sum("value"))
            .order_by("paid_for__name")
        )


class MoneySpentTrendPartialView(RoomChildTransactionQuerysetMixin, DebtBaseContext, generic.TemplateView):
    template_name = "transaction/partials/_money_spent_trend.html"

    PERIOD_OPTIONS = {
        "1w": {"label": "Last 7 days", "weeks": 1, "button_label": "7d"},
        "4w": {"label": "Last 4 weeks", "weeks": 4, "button_label": "4w"},
        "12w": {"label": "Last 12 weeks", "weeks": 12, "button_label": "12w"},
        "last-activity": {
            "label": "Relative to last activity",
            "button_label": "Last activity",
            "weeks": 12,
            "relative": True,
        },
    }
    DEFAULT_PERIOD = "last-activity"

    def get_period_key(self):
        period = self.request.GET.get("period", self.DEFAULT_PERIOD)
        if period not in self.PERIOD_OPTIONS:
            return self.DEFAULT_PERIOD
        return period

    def _build_timeseries(self):
        period_key = self.get_period_key()
        period_config = self.PERIOD_OPTIONS[period_key]
        now = timezone.localtime(timezone.now())

        base_qs = self.get_base_queryset()
        if period_config.get("relative"):
            latest_paid_at = (
                base_qs.order_by("-parent_transaction__paid_at")
                .values_list("parent_transaction__paid_at", flat=True)
                .first()
            )
            if latest_paid_at:
                latest_dt = timezone.localtime(latest_paid_at)
                raw_end = latest_dt
                raw_start = latest_dt - timedelta(weeks=period_config["weeks"])
            else:
                raw_end = now
                raw_start = now - timedelta(weeks=period_config["weeks"])
        else:
            raw_end = now
            raw_start = now - timedelta(weeks=period_config["weeks"])

        start_week = raw_start - timedelta(days=raw_start.weekday())
        start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
        last_monday = raw_end - timedelta(days=raw_end.weekday())
        queryset = (
            base_qs.filter(parent_transaction__paid_at__gte=start_week, parent_transaction__paid_at__lte=raw_end)
            .annotate(week=TruncWeek("parent_transaction__paid_at"))
            .values("week", "parent_transaction__currency__sign")
            .annotate(
                currency_sign=F("parent_transaction__currency__sign"),
                weekly_total=Sum("value"),
            )
            .order_by("week")
        )

        bucket_totals = {}
        currency_sign = ""
        for row in queryset:
            week_start = timezone.localtime(row["week"]).date()
            bucket_totals[week_start] = row["weekly_total"]
            currency_sign = currency_sign or row["currency_sign"]

        current_week = start_week.date()
        final_week = last_monday.date()
        cumulative_total = Decimal("0")
        timeseries = []
        max_cumulative = Decimal("0")

        while current_week <= final_week:
            weekly_total = bucket_totals.get(current_week, Decimal("0"))
            cumulative_total += weekly_total
            timeseries.append(
                {
                    "label": current_week.strftime("%d %b"),
                    "week_start": current_week,
                    "weekly_total": weekly_total,
                    "cumulative_total": cumulative_total,
                }
            )
            if cumulative_total > max_cumulative:
                max_cumulative = cumulative_total
            current_week += timedelta(weeks=1)

        point_count = len(timeseries)
        for index, point in enumerate(timeseries):
            if max_cumulative == 0:
                point["height"] = 0
            else:
                point["height"] = round((point["cumulative_total"] / max_cumulative) * 100)
            point["chart_y"] = 100 - point["height"]

            position = (
                Decimal("0") if point_count <= 1 else (Decimal(index) * Decimal("100")) / Decimal(point_count - 1)
            )
            point["position"] = float(position.quantize(Decimal("0.01")))
            point["cumulative_float"] = float(point["cumulative_total"])
            point["week_iso"] = point["week_start"].isoformat()

        return {
            "points": timeseries,
            "currency_sign": currency_sign,
            "max_value": max_cumulative,
            "range_start": start_week.date(),
            "range_end": raw_end.date(),
            "period_label": period_config["label"],
        }

    def get_timeseries_payload(self):
        if not hasattr(self, "_timeseries_cache"):
            self._timeseries_cache = self._build_timeseries()
        return self._timeseries_cache

    @context
    @property
    def period_options(self):
        active = self.get_period_key()
        return [
            {
                "key": key,
                "label": cfg["label"],
                "button_label": cfg.get("button_label", cfg["label"]),
                "is_wide": cfg.get("relative", False),
                "active": key == active,
            }
            for key, cfg in self.PERIOD_OPTIONS.items()
        ]

    @context
    @property
    def trend_period_label(self):
        return self.PERIOD_OPTIONS[self.get_period_key()]["label"]

    @context
    @property
    def timeseries(self):
        return self.get_timeseries_payload()["points"]

    @context
    @property
    def trend_currency_sign(self):
        return self.get_timeseries_payload()["currency_sign"]

    @context
    @property
    def timeseries_max_value(self):
        return self.get_timeseries_payload()["max_value"]

    @context
    @property
    def trend_range_start(self):
        return self.get_timeseries_payload()["range_start"]

    @context
    @property
    def trend_range_end(self):
        return self.get_timeseries_payload()["range_end"]

    @context
    @property
    def trend_chart_points(self):
        return [
            {"date": point["week_iso"], "label": point["label"], "value": point["cumulative_float"]}
            for point in self.get_timeseries_payload()["points"]
        ]
