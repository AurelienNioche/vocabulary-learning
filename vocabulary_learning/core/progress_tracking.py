"""Progress tracking functionality for vocabulary learning."""

import random
from datetime import datetime
from typing import Callable, Dict, Optional

import pytz


def get_utc_now():
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(pytz.UTC)


def calculate_next_interval(current_interval: float, easiness_factor: float) -> float:
    """Calculate the next review interval based on the SuperMemo 2 algorithm.

    Args:
        current_interval: Current interval in hours
        easiness_factor: Current easiness factor

    Returns:
        Next interval in hours
    """
    if current_interval == 0:
        return 0.0333  # First success: wait 2 minutes
    elif current_interval == 0.0333:
        return 24  # Second success: wait 1 day
    else:
        return current_interval * easiness_factor  # Increase interval based on easiness


def update_progress(word_id: str, success: bool, progress: Dict, save_callback: Callable) -> None:
    """Update progress for a word after a practice attempt.

    Args:
        word_id: ID of the word
        success: Whether the attempt was successful
        progress: Progress dictionary to update
        save_callback: Function to call to save progress
    """
    now = get_utc_now()

    # Initialize word data if not present
    if word_id not in progress:
        progress[word_id] = {
            "attempts": 0,
            "successes": 0,
            "interval": 0,  # Start with 0 interval
            "last_attempt_was_failure": False,
            "last_seen": now.isoformat(),
            "review_intervals": [],
            "easiness_factor": 2.5,  # Initial easiness factor
            "attempt_history": [],  # List of (timestamp, success) tuples
        }

    # Calculate time since last review
    if "last_seen" in progress[word_id]:
        last_seen = datetime.fromisoformat(progress[word_id]["last_seen"])
        if last_seen.tzinfo is None:
            last_seen = pytz.UTC.localize(last_seen)
        hours_since_last = (now - last_seen).total_seconds() / 3600.0
        progress[word_id]["review_intervals"].append(hours_since_last)

    # Update statistics
    progress[word_id]["attempts"] += 1
    if success:
        progress[word_id]["successes"] += 1

    # Add attempt to history
    if "attempt_history" not in progress[word_id]:
        progress[word_id]["attempt_history"] = []
    progress[word_id]["attempt_history"].append({"timestamp": now.isoformat(), "success": success})

    # Update easiness factor and interval
    if success:
        progress[word_id]["interval"] = calculate_next_interval(
            progress[word_id]["interval"],
            progress[word_id]["easiness_factor"],
        )
        # Only increase easiness factor if it's not already at maximum
        if progress[word_id]["easiness_factor"] < 2.5:
            progress[word_id]["easiness_factor"] = min(
                progress[word_id]["easiness_factor"] + 0.1, 2.5
            )
    else:
        progress[word_id]["interval"] = 0.0333  # Reset to 2 minutes on failure
        progress[word_id]["easiness_factor"] = max(progress[word_id]["easiness_factor"] - 0.2, 1.3)

    # Update last seen and failure status
    progress[word_id]["last_seen"] = now.isoformat()
    progress[word_id]["last_attempt_was_failure"] = not success

    # Save progress
    save_callback()


def calculate_weighted_success_rate(attempt_history: list, now: Optional[datetime] = None) -> float:
    """Calculate success rate with temporal decay weighting.

    More recent attempts have more weight in the calculation.
    Uses an exponential decay function with a half-life of 30 days.

    Args:
        attempt_history: List of attempts with timestamps and success status
        now: Current time (defaults to UTC now if not provided)

    Returns:
        Weighted success rate between 0 and 1
    """
    if not attempt_history:
        return 0.0

    if now is None:
        now = get_utc_now()

    HALF_LIFE_DAYS = 30.0  # Time after which an attempt's weight becomes 0.5
    decay_rate = 0.693 / (HALF_LIFE_DAYS * 24)  # ln(2) / half-life in hours

    total_weight = 0.0
    weighted_successes = 0.0

    for attempt in attempt_history:
        timestamp = datetime.fromisoformat(attempt["timestamp"])
        if timestamp.tzinfo is None:
            timestamp = pytz.UTC.localize(timestamp)

        hours_ago = (now - timestamp).total_seconds() / 3600.0
        weight = 2.718 ** (-decay_rate * hours_ago)  # e^(-λt)

        total_weight += weight
        if attempt["success"]:
            weighted_successes += weight

    if total_weight == 0:
        return 0.0

    return weighted_successes / total_weight


def calculate_priority(word_data: Optional[Dict], active_words_count: int) -> float:
    """Calculate priority score for a word.

    Args:
        word_data: Word's progress data
        active_words_count: Number of active learning words

    Returns:
        Priority score (0.0 to 1.0)
    """
    # For new words, check if we have space for more active words
    if word_data is None:
        if active_words_count < 8:  # Maximum 8 active words
            return 1.0
        return 0.0

    # Skip if no interval set
    if "interval" not in word_data:
        return 0.0

    # Calculate time since last review
    last_seen = datetime.fromisoformat(word_data["last_seen"])
    # Ensure both datetimes are timezone-aware
    now = get_utc_now()
    if last_seen.tzinfo is None:  # Handle old timestamps
        last_seen = pytz.UTC.localize(last_seen)
    hours_since_last = (now - last_seen).total_seconds() / 3600.0

    # Calculate priority based on how overdue the word is
    interval = word_data["interval"]
    if interval == 0:
        return 0.0

    overdue_ratio = hours_since_last / interval
    priority = max(0.0, overdue_ratio)

    # Add bonus for failed words
    if word_data.get("last_attempt_was_failure", False):
        priority += 0.3

    return min(1.0, priority)


def is_mastered(word_data: Dict) -> bool:
    """Check if a word meets the mastery criteria.

    A word is considered mastered if:
    1. It has at least 5 successful reviews total
    2. It has a weighted success rate of at least 80%, with more recent attempts weighted more heavily

    Args:
        word_data: Dictionary containing word progress data

    Returns:
        True if the word is mastered, False otherwise
    """
    if not word_data:
        return False

    successes = word_data.get("successes", 0)
    attempt_history = word_data.get("attempt_history", [])

    # First criterion: at least 5 successful reviews total
    if successes < 5:
        return False

    # Second criterion: 80% weighted success rate
    weighted_success_rate = calculate_weighted_success_rate(attempt_history)
    return weighted_success_rate >= 0.8


def count_active_learning_words(progress_data: Dict) -> int:
    """Count how many words are being actively learned.

    A word is considered "active" if it hasn't been mastered yet.

    Args:
        progress_data: Dictionary of word progress data

    Returns:
        Number of active words
    """
    active_count = 0

    for word_data in progress_data.values():
        # Skip if no attempts
        if word_data.get("attempts", 0) == 0:
            continue

        # A word is active if it's not mastered
        if not is_mastered(word_data):
            active_count += 1

    return active_count
