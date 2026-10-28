"""Interpret Claude OAuth extra_usage without inventing a cash balance.

The endpoint is not a stable public API. Amounts are deliberately used only
as a ratio: no currency or monetary unit is assumed.
"""
import math


def nonnegative(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def normalize_extra_usage(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('is_enabled'), bool):
        return None
    enabled = raw['is_enabled']
    used = nonnegative(raw.get('used_credits'))
    cap = nonnegative(raw.get('monthly_limit'))
    percent = None
    if used is not None and cap is not None and cap > 0:
        percent = used / cap
    elif cap is None:
        utilization = nonnegative(raw.get('utilization'))
        if utilization is not None:
            percent = utilization / 100
    # Zero cap is not interpreted as unlimited or as proof of zero funds.
    return {'enabled': enabled, 'percent': percent}
