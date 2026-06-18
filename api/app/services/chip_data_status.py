from __future__ import annotations

from datetime import date, timedelta
from typing import Any


CHIP_LOOKBACK_TRADING_DAYS = 5


def trading_day_candidates(target: date, count: int = CHIP_LOOKBACK_TRADING_DAYS) -> list[date]:
    candidates: list[date] = []
    candidate = target
    while len(candidates) < count:
        if candidate.weekday() < 5:
            candidates.append(candidate)
        candidate -= timedelta(days=1)
    return candidates


def apply_data_status(result: dict[str, Any], target: date) -> dict[str, Any]:
    data_date = result.get("dataDate") or result.get("asOfDate")
    result["dataDate"] = data_date
    result["asOfDate"] = data_date
    if not data_date or result.get("dataGaps"):
        result["status"] = "missing"
    else:
        result["status"] = "current" if data_date == target.isoformat() else "latest_available"
    return result


def has_usable_data(result: dict[str, Any]) -> bool:
    return bool(result.get("dataDate") or result.get("asOfDate")) and not result.get("dataGaps")
