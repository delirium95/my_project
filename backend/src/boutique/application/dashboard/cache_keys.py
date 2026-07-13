from datetime import date

_DASHBOARD_CACHE_PREFIX = "dashboard:v1:"


def dashboard_cache_prefix() -> str:
    """Return the versioned prefix for every dashboard read model."""
    return _DASHBOARD_CACHE_PREFIX


def dashboard_summary_cache_key() -> str:
    return f"{_DASHBOARD_CACHE_PREFIX}summary"


def monthly_revenue_cache_key(*, start_date: date | None, end_date: date | None) -> str:
    start = start_date.isoformat() if start_date else "all"
    end = end_date.isoformat() if end_date else "all"
    return f"{_DASHBOARD_CACHE_PREFIX}revenue:{start}:{end}"
