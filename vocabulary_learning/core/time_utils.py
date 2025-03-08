"""Utilities for time formatting and calculations."""


def format_time_interval(hours: float) -> str:
    """Format time interval in days, hours, and minutes.

    Formats a time interval given in hours into a human-readable string.
    Only shows the relevant units (e.g., only minutes if < 1h, only hours and minutes if < 1d).
    For very short intervals (< 1 minute), shows seconds.

    Args:
        hours: Time interval in hours

    Returns
    -------
        Human-readable string representation of the time interval
    """
    if hours == 0:
        return "as soon as possible"

    # Convert to minutes and handle sub-minute intervals
    total_minutes = hours * 60

    if total_minutes < 1:
        seconds = round(total_minutes * 60)
        return f"{seconds} seconds"

    # Round to nearest minute to avoid floating point imprecision
    total_minutes = round(total_minutes)
    days = total_minutes // (24 * 60)
    remaining_minutes = total_minutes % (24 * 60)
    hours_part = remaining_minutes // 60
    minutes = remaining_minutes % 60

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours_part > 0:
        parts.append(f"{hours_part} hour{'s' if hours_part > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

    if len(parts) > 1:
        return f"{', '.join(parts[:-1])} and {parts[-1]}"
    return parts[0] if parts else "less than 1 minute"
