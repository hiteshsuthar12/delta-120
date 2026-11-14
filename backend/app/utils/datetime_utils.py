from datetime import datetime, timezone
import zoneinfo

def now_utc() -> datetime:
    """Return current datetime in UTC."""
    return datetime.now(timezone.utc)

def now_utc_iso() -> str:
    """Return ISO format string of current UTC time."""
    return now_utc().isoformat()

def get_current_trading_day(tz_name: str = "Asia/Kolkata") -> str:
    """
    Get the trading day string (YYYY-MM-DD) based on configured timezone.
    Daily reset occurs at 00:00:00 in the target timezone.
    """
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    local_time = datetime.now(tz)
    return local_time.strftime("%Y-%m-%d")

def format_timestamp(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

