from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools._shared import err


WEEKDAYS_VI = ["Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Thứ bảy", "Chủ nhật"]


def current_datetime(tz: str = "local") -> dict[str, Any]:
    try:
        tz = (tz or "local").strip().lower()
        if tz == "local":
            now = datetime.now()
            zone = "local"
        elif tz in {"utc", "gmt"}:
            now = datetime.now(timezone.utc)
            zone = "utc"
        else:
            raise ValueError("tz must be 'local' or 'utc' (custom timezones are not supported)")
        return {
            "tool": "current_datetime",
            "tz": zone,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday_vi": WEEKDAYS_VI[now.weekday()],
            "note": "Use this to anchor relative time words like 'hôm nay', 'tuần này' before calling lookup.",
        }
    except Exception as exc:
        return err("current_datetime", exc)
