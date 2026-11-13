import datetime as dt
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

# Keep all test writes inside this worktree.
TEST_ROOT = Path(__file__).resolve().parents[3] / ".fieldshift" / "tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["FIELDSHIFT_DATA_DIR"] = tempfile.mkdtemp(prefix="run-", dir=TEST_ROOT)


@pytest.fixture(autouse=True)
def offline_outlook(monkeypatch):
    from fieldshift.infrastructure.data_sources import glofas
    from fieldshift.infrastructure.data_sources.forecasts import open_meteo_seasonal

    class DemoDate(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 13)

    class DemoDatetime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            instant = cls(2026, 11, 13, 14, tzinfo=dt.timezone.utc)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    clock = SimpleNamespace(
        date=DemoDate, datetime=DemoDatetime, timezone=dt.timezone, timedelta=dt.timedelta
    )
    monkeypatch.setattr(glofas, "dt", clock)
    monkeypatch.setattr(open_meteo_seasonal, "dt", clock)

    def offline(*args, **kwargs):
        raise httpx.ConnectError("Unit/integration suite runs offline")

    monkeypatch.setattr(httpx, "get", offline)
