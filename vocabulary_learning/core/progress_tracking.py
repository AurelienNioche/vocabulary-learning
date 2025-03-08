"""Progress tracking functionality for vocabulary learning."""

from datetime import datetime
from typing import Callable, Dict, Optional

import pytz

from vocabulary_learning.core.constants import (
    EASINESS_DECREASE,
    EASINESS_INCREASE,
    FAILED_WORD_PRIORITY_BONUS,
    FIRST_SUCCESS_INTERVAL,
    HALF_LIFE_DAYS,
    INITIAL_EASINESS_FACTOR,
    MASTERY_MIN_SUCCESSES,
    MASTERY_SUCCESS_RATE,
    MAX_ACTIVE_WORDS,
    MIN_EASINESS_FACTOR,
    SECOND_SUCCESS_INTERVAL,
)


def get_utc_now():
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(pytz.UTC)


def calculate_next_interval(
    current_interval: float, easiness_factor: float, hours_since_last: float = None
) -> float:
    """Calculate the next review interval based on the SuperMemo 2 algorithm.

    Args:
        current_interval: Current interval in hours
        easiness_factor: Current easiness factor
        hours_since_last: Hours elapsed since the word was last seen

    Returns
    -------
        Next interval in hours
    """
    if current_interval == 0:
        return FIRST_SUCCESS_INTERVAL  # First success: wait 2 minutes
    elif current_interval == FIRST_SUCCESS_INTERVAL:
        return SECOND_SUCCESS_INTERVAL  # Second success: wait 1 day
    else:
        # If time since last seen is provided and valid, use it instead of current interval
        if hours_since_last and hours_since_last > 0:
            return (
                hours_since_last * easiness_factor
            )  # Use actual elapsed time for calculation
        else:
            return current_interval * easiness_factor  # Fallback to original algorithm


def update_progress(
    word_id: str, success: bool, progress: Dict, save_callback: Callable
) -> None:
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
            "easiness_factor": INITIAL_EASINESS_FACTOR,
            "attempt_history": [],
            "first_introduced": now.isoformat(),  # Track first introduction date
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
    progress[word_id]["attempt_history"].append(
        {"timestamp": now.isoformat(), "success": success}
    )

    # Update easiness factor and interval
    if success:
        progress[word_id]["interval"] = calculate_next_interval(
            progress[word_id]["interval"],
            progress[word_id]["easiness_factor"],
            hours_since_last,
        )
        # Only increase easiness factor if it's not already at maximum
        if progress[word_id]["easiness_factor"] < INITIAL_EASINESS_FACTOR:
            progress[word_id]["easiness_factor"] = min(
                progress[word_id]["easiness_factor"] + EASINESS_INCREASE,
                INITIAL_EASINESS_FACTOR,
            )
    else:
        progress[word_id]["interval"] = (
            FIRST_SUCCESS_INTERVAL  # Reset to 2 minutes on failure
        )
        progress[word_id]["easiness_factor"] = max(
            progress[word_id]["easiness_factor"] - EASINESS_DECREASE,
            MIN_EASINESS_FACTOR,
        )

    # Update last seen and failure status
    progress[word_id]["last_seen"] = now.isoformat()
    progress[word_id]["last_attempt_was_failure"] = not success

    # Save progress
    save_callback()


def calculate_weighted_success_rate(
    attempt_history: list, now: Optional[datetime] = None
) -> float:
    """Calculate success rate with temporal decay weighting.

    More recent attempts have more weight in the calculation.
    Uses an exponential decay function with a half-life of 30 days.

    Args:
        attempt_history: List of attempts with timestamps and success status
        now: Current time (defaults to UTC now if not provided)

    Returns
    -------
        Weighted success rate between 0 and 1
    """
    if not attempt_history:
        return 0.0

    if now is None:
        now = get_utc_now()

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

    Returns
    -------
        Priority score (0.0 to 1.0)
    """
    # For new words, check if we have space for more active words
    if word_data is None:
        if active_words_count < MAX_ACTIVE_WORDS:  # Maximum active words
            # Give new words a good priority, but not higher than overdue words
            return 0.8
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
        priority += FAILED_WORD_PRIORITY_BONUS

    # Cap priority at 1.0
    return min(1.0, priority)


def is_mastered(word_data: Dict) -> bool:
    """Check if a word meets the mastery criteria.

    A word is considered mastered if:
    1. It has at least MASTERY_MIN_SUCCESSES successful reviews total
    2. It has a weighted success rate of at least MASTERY_SUCCESS_RATE

    Args:
        word_data: Dictionary containing word progress data

    Returns
    -------
        True if the word is mastered, False otherwise
    """
    if not word_data:
        return False

    successes = word_data.get("successes", 0)
    attempt_history = word_data.get("attempt_history", [])

    # First criterion: minimum number of successful reviews
    if successes < MASTERY_MIN_SUCCESSES:
        return False

    # Second criterion: minimum weighted success rate
    weighted_success_rate = calculate_weighted_success_rate(attempt_history)
    return weighted_success_rate >= MASTERY_SUCCESS_RATE


def count_active_learning_words(progress_data: Dict) -> int:
    """Count the number of words actively being learned.

    Args:
        progress_data: Progress data dictionary

    Returns
    -------
        Number of active words
    """
    return sum(
        1
        for word_id, data in progress_data.items()
        if not is_mastered(data) and data["attempts"] > 0
    )


def is_newly_introduced(word_data: Dict) -> bool:
    """Check if a word was just introduced for the first time.

    A word is considered newly introduced if it has only one attempt in its history.

    Args:
        word_data: Word progress data

    Returns
    -------
        True if the word was just introduced, False otherwise
    """
    if "attempts" not in word_data:
        return False
    return word_data["attempts"] == 1
