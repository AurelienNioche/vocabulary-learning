"""Progress tracking functionality for vocabulary learning."""

import random
from datetime import datetime
from typing import Dict, Optional

import pytz


def get_utc_now():
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(pytz.UTC)


def update_progress(word_id: str, success: bool, progress: Dict, save_callback):
    """Update progress for a given word and sync with Firebase.

    Args:
        word_id: The word ID (e.g., 'word_000001')
        success: Whether the attempt was successful
        progress: Progress dictionary
        save_callback: Function to call to save progress
    """
    if word_id not in progress:
        progress[word_id] = {
            "attempts": 0,
            "successes": 0,
            "last_seen": get_utc_now().isoformat(),
            "review_intervals": [],
            "last_attempt_was_failure": False,
            "easiness_factor": 2.5,  # Initial easiness factor for SuperMemo 2
            "interval": 0,  # Current interval in hours
        }
    elif "interval" not in progress[word_id]:
        # Add interval if missing in existing progress data
        progress[word_id]["interval"] = 0
        progress[word_id]["easiness_factor"] = progress[word_id].get("easiness_factor", 2.5)
        progress[word_id]["last_attempt_was_failure"] = progress[word_id].get(
            "last_attempt_was_failure", False
        )

    # Calculate and store interval since last review
    last_seen = datetime.fromisoformat(progress[word_id]["last_seen"])
    if last_seen.tzinfo is None:  # Handle old timestamps
        last_seen = pytz.UTC.localize(last_seen)
    hours_since_last = (get_utc_now() - last_seen).total_seconds() / 3600.0
    progress[word_id]["review_intervals"].append(hours_since_last)

    # Keep only last 10 intervals to track progress
    if len(progress[word_id]["review_intervals"]) > 10:
        progress[word_id]["review_intervals"] = progress[word_id]["review_intervals"][-10:]

    progress[word_id]["attempts"] += 1
    if success:
        progress[word_id]["successes"] += 1
        # Update SuperMemo 2 parameters
        if progress[word_id]["interval"] == 0:
            progress[word_id]["interval"] = 0.0333  # First success: wait 2 minutes
        elif progress[word_id]["interval"] == 0.0333:
            progress[word_id]["interval"] = 24  # Second success: wait 1 day
        else:
            # Calculate new interval using easiness factor
            progress[word_id]["interval"] *= progress[word_id]["easiness_factor"]

        # Update easiness factor (increase for correct answers)
        progress[word_id]["easiness_factor"] = max(1.3, progress[word_id]["easiness_factor"] + 0.1)
        progress[word_id]["last_attempt_was_failure"] = False
    else:
        # Decrease interval and easiness factor for incorrect answers
        progress[word_id]["interval"] = max(
            0.0333, progress[word_id]["interval"] * 0.5
        )  # Minimum 2 minutes
        progress[word_id]["easiness_factor"] = max(1.3, progress[word_id]["easiness_factor"] - 0.2)
        progress[word_id]["last_attempt_was_failure"] = True

    progress[word_id]["last_seen"] = get_utc_now().isoformat()

    # Save progress immediately after update
    save_callback()


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


def count_active_learning_words(progress_data: Dict) -> int:
    """Count how many words are being actively learned.

    A word is considered "active" if it hasn't been mastered yet.
    A word is considered mastered if:
    1. It has at least 5 successful reviews
    2. It has a success rate of at least 90%

    Args:
        progress_data: Dictionary of word progress data

    Returns:
        Number of active words
    """
    active_count = 0

    for word_data in progress_data.values():
        # Skip if no attempts
        attempts = word_data.get("attempts", 0)
        if attempts == 0:
            continue

        # Check mastery criteria
        successes = word_data.get("successes", 0)
        success_rate = successes / attempts

        # A word is active if it's not mastered
        if success_rate < 0.9 or successes < 5:
            active_count += 1

    return active_count
