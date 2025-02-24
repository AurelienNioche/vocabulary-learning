"""Utilities for text processing and normalization."""

import os
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

import pytz
from dotenv import load_dotenv

from vocabulary_learning.core.constants import DEFAULT_TIMEZONE, TYPO_SIMILARITY_THRESHOLD


def normalize_french(text):
    """Remove accents and normalize French text."""
    # Convert to lowercase and strip
    text = text.lower().strip()
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    # Remove diacritics
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def is_minor_typo(str1, str2, threshold=TYPO_SIMILARITY_THRESHOLD):
    """Check if two strings are similar enough to be considered a typo."""
    return SequenceMatcher(None, str1, str2).ratio() > threshold


def format_datetime(dt_str):
    """Format datetime string with timezone support.

    Converts UTC datetime to local timezone and formats it in a human-readable way.
    For recent dates, uses relative formatting (e.g., "Today at 14:30", "Yesterday at 09:15").
    For older dates, uses absolute formatting with the local timezone.
    """
    load_dotenv()
    timezone_str = os.getenv("TIMEZONE", DEFAULT_TIMEZONE)
    timezone = pytz.timezone(timezone_str)

    try:
        dt = datetime.fromisoformat(dt_str)
        # All timestamps in progress.json are in UTC
        utc_dt = pytz.utc.localize(dt) if dt.tzinfo is None else dt.astimezone(pytz.UTC)
        # Convert to local timezone
        local_dt = utc_dt.astimezone(timezone)
        now = datetime.now(timezone)

        # Calculate the date difference
        date_diff = (now.date() - local_dt.date()).days

        # Format based on how recent the date is
        if date_diff == 0:
            return f"Today at {local_dt.strftime('%H:%M')} ({timezone_str})"
        elif date_diff == 1:
            return f"Yesterday at {local_dt.strftime('%H:%M')} ({timezone_str})"
        elif date_diff < 7:
            return f"{local_dt.strftime('%A')} at {local_dt.strftime('%H:%M')} ({timezone_str})"
        else:
            return f"{local_dt.strftime('%Y-%m-%d %H:%M')} ({timezone_str})"
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_str


def format_time_interval(hours):
    """Format a time interval in hours into a human-readable string."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if hours != 1 else ''}"
    else:
        days = hours / 24
        return f"{int(days)} day{'s' if days != 1 else ''}"
