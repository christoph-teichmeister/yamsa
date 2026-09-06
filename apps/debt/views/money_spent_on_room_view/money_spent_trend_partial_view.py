from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import formats, timezone
from django.views import generic
from django_context_decorator import context

from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.debt.views.money_spent_on_room_view.room_child_transaction_queryset_mixin import (
    RoomChildTransactionQuerysetMixin,
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

    def get_period_key(self) -> str:
        period = self.request.GET.get("period", self.DEFAULT_PERIOD)
        if period not in self.PERIOD_OPTIONS:
            return self.DEFAULT_PERIOD
        return period

    def _resolve_range(self) -> tuple[datetime, datetime]:
        period_config = self.PERIOD_OPTIONS[self.get_period_key()]
        now = timezone.localtime(timezone.now())

        end = now
        if period_config.get("relative"):
            latest_paid_at = (
                self.get_base_queryset()
                .order_by("-parent_transaction__paid_at")
                .values_list("parent_transaction__paid_at", flat=True)
                .first()
            )
            if latest_paid_at:
                end = timezone.localtime(latest_paid_at)

        return end - timedelta(weeks=period_config["weeks"]), end

    def _baseline_per_currency(self, range_start: datetime) -> dict[str, Decimal]:
        """Total spent before the window - the level each series starts from."""
        rows = (
            self.get_base_queryset()
            .filter(parent_transaction__paid_at__lt=range_start)
            .values("parent_transaction__currency__sign")
            .annotate(currency_sign=F("parent_transaction__currency__sign"), total=Sum("value"))
        )
        return {row["currency_sign"]: row["total"] for row in rows}

    def _expenses_in_range(self, range_start: datetime, range_end: datetime):
        """One row per parent transaction: the chart steps per expense, not per calendar bucket."""
        return (
            self.get_base_queryset()
            .filter(parent_transaction__paid_at__gte=range_start, parent_transaction__paid_at__lte=range_end)
            .values(
                "parent_transaction_id",
                "parent_transaction__paid_at",
                "parent_transaction__currency__sign",
            )
            .annotate(currency_sign=F("parent_transaction__currency__sign"), expense_total=Sum("value"))
            .order_by("parent_transaction__paid_at", "parent_transaction_id")
        )

    @staticmethod
    def _point(moment: datetime, cumulative: Decimal, delta: Decimal) -> dict:
        return {
            "date": moment.replace(tzinfo=None).isoformat(timespec="seconds"),
            "label": formats.date_format(moment, "SHORT_DATETIME_FORMAT"),
            "value": float(cumulative),
            "delta": float(delta),
        }

    def _build_timeseries(self) -> dict:
        range_start, range_end = self._resolve_range()
        baselines = self._baseline_per_currency(range_start)

        # Currencies are never summed into one line: a EUR and a HUF total share no scale, so each
        # gets its own series (and its own axis in the chart).
        cumulative_per_currency = dict(baselines)
        points_per_currency: dict[str, list[dict]] = {
            sign: [self._point(range_start, total, Decimal("0"))] for sign, total in baselines.items()
        }

        for row in self._expenses_in_range(range_start, range_end):
            sign = row["currency_sign"]
            expense_total = row["expense_total"]
            if sign not in points_per_currency:
                points_per_currency[sign] = [self._point(range_start, Decimal("0"), Decimal("0"))]
                cumulative_per_currency[sign] = Decimal("0")
            cumulative_per_currency[sign] += expense_total
            points_per_currency[sign].append(
                self._point(
                    timezone.localtime(row["parent_transaction__paid_at"]),
                    cumulative_per_currency[sign],
                    expense_total,
                )
            )

        series = []
        for sign, points in points_per_currency.items():
            cumulative = cumulative_per_currency[sign]
            points.append(self._point(range_end, cumulative, Decimal("0")))
            series.append(
                {
                    "currency": sign,
                    "points": points,
                    "baseline": float(baselines.get(sign, Decimal("0"))),
                    "total": float(cumulative),
                }
            )
        series.sort(key=lambda entry: (-entry["total"], entry["currency"]))

        return {
            "series": series,
            "range_start": range_start,
            "range_end": range_end,
            "period_label": self.PERIOD_OPTIONS[self.get_period_key()]["label"],
        }

    def get_timeseries_payload(self) -> dict:
        if not hasattr(self, "_timeseries_cache"):
            self._timeseries_cache = self._build_timeseries()
        return self._timeseries_cache

    @context
    @property
    def period_options(self) -> list[dict]:
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
    def trend_period_label(self) -> str:
        return self.get_timeseries_payload()["period_label"]

    @context
    @property
    def trend_series(self) -> list[dict]:
        return self.get_timeseries_payload()["series"]

    @context
    @property
    def trend_range_start(self) -> datetime:
        return self.get_timeseries_payload()["range_start"]

    @context
    @property
    def trend_range_end(self) -> datetime:
        return self.get_timeseries_payload()["range_end"]

    @context
    @property
    def trend_chart_data(self) -> dict:
        payload = self.get_timeseries_payload()
        return {
            "rangeStart": payload["range_start"].replace(tzinfo=None).isoformat(timespec="seconds"),
            "rangeEnd": payload["range_end"].replace(tzinfo=None).isoformat(timespec="seconds"),
            "series": [{"currency": entry["currency"], "points": entry["points"]} for entry in payload["series"]],
        }
