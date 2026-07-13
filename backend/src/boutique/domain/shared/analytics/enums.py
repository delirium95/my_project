from enum import StrEnum


class AnalyticsEvent(StrEnum):
    DASHBOARD_VIEWED = "dashboard_viewed"
    FILTER_APPLIED = "filter_applied"
    CHART_DRILLED_DOWN = "chart_drilled_down"
    ORDERS_EXPORTED = "orders_exported"
