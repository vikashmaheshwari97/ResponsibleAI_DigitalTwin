from datetime import datetime, timedelta, timezone

from services.analytics_service import duration_seconds


def test_duration_seconds():
    start = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(seconds=42.5)
    assert duration_seconds(start, end) == 42.5


def test_duration_missing_endpoint():
    assert duration_seconds(None, None) is None
