"""Progress tracking functionality for vocabulary learning."""

import random
from datetime import datetime
from typing import Dict, Optional


def update_progress(word, success, progress, save_callback):
    """Update progress for a given word and sync with Firebase."""
    if word not in progress:
        progress[word] = {
            "attempts": 0,
            "successes": 0,
            "last_seen": datetime.now().isoformat(),
            "review_intervals": [],
            "last_attempt_was_failure": False,
            "easiness_factor": 2.5,  # Initial easiness factor for SuperMemo 2
            "interval": 0,  # Current interval in hours
        }
    elif "interval" not in progress[word]:
        # Add interval if missing in existing progress data
        progress[word]["interval"] = 0
        progress[word]["easiness_factor"] = progress[word].get("easiness_factor", 2.5)
        progress[word]["last_attempt_was_failure"] = progress[word].get(
            "last_attempt_was_failure", False
        )

    # Calculate and store interval since last review
    last_seen = datetime.fromisoformat(progress[word]["last_seen"])
    hours_since_last = (datetime.now() - last_seen).total_seconds() / 3600.0
    progress[word]["review_intervals"].append(hours_since_last)

    # Keep only last 10 intervals to track progress
    if len(progress[word]["review_intervals"]) > 10:
        progress[word]["review_intervals"] = progress[word]["review_intervals"][-10:]

    progress[word]["attempts"] += 1
    if success:
        progress[word]["successes"] += 1
        # Update SuperMemo 2 parameters
        if progress[word]["interval"] == 0:
            progress[word]["interval"] = 0.0833  # First success: wait 5 minutes
        elif progress[word]["interval"] == 0.0833:
            progress[word]["interval"] = 24  # Second success: wait 1 day
        else:
            # Calculate new interval using easiness factor
            progress[word]["interval"] *= progress[word]["easiness_factor"]

        # Update easiness factor (increase for correct answers)
        progress[word]["easiness_factor"] = max(1.3, progress[word]["easiness_factor"] + 0.1)
    else:
        # Decrease interval and easiness factor for incorrect answers
        progress[word]["interval"] = max(
            0.0833, progress[word]["interval"] * 0.5
        )  # Minimum 5 minutes
        progress[word]["easiness_factor"] = max(1.3, progress[word]["easiness_factor"] - 0.2)
        progress[word]["last_attempt_was_failure"] = True

    progress[word]["last_seen"] = datetime.now().isoformat()

    # Save progress immediately after update
    save_callback()


def calculate_priority(word_data: Optional[Dict], active_words_count: int) -> float:
    """Calculate priority score for a word.

    The priority score is based on several factors:
    1. Time since last review (higher priority for words not seen in a while)
    2. Success rate (higher priority for words with lower success rates)
    3. Number of attempts (higher priority for newer words)
    4. Last attempt result (higher priority for words that failed last time)
    5. Current interval from SuperMemo 2 algorithm

    Args:
        word_data: Word progress data or None if no progress
        active_words_count: Number of words being actively learned

    Returns:
        Priority score (higher means higher priority)
    """
    if not word_data:
        # New words get high priority, but not maximum
        # This ensures some balance between new and review words
        return 0.8

    # Calculate time factor
    time_factor = 0.0
    if word_data.get("last_seen"):
        try:
            last_seen = datetime.fromisoformat(word_data["last_seen"])
            hours_since = (datetime.now() - last_seen).total_seconds() / 3600.0
            scheduled_interval = word_data.get("interval", 0)

            if hours_since >= scheduled_interval:
                # Word is due or overdue
                time_factor = min(2.0, 1.0 + (hours_since - scheduled_interval) / 24.0)
            else:
                # Word is not due yet
                time_factor = hours_since / scheduled_interval
        except (ValueError, TypeError):
            time_factor = 1.0
    else:
        # Never seen words get high time factor
        time_factor = 0.9

    # Calculate success rate factor (lower success rate = higher priority)
    success_rate = (
        word_data["successes"] / word_data["attempts"] if word_data.get("attempts", 0) > 0 else 0.0
    )
    success_factor = 1.0 - (success_rate * 0.5)  # Scale to [0.5, 1.0]

    # Calculate attempts factor (fewer attempts = higher priority)
    attempts = word_data.get("attempts", 0)
    attempts_factor = 1.0 / (1.0 + attempts / 10.0)  # Decay with more attempts

    # Factor in last attempt result
    last_attempt_factor = 1.2 if word_data.get("last_attempt_was_failure") else 1.0

    # Calculate final priority score
    base_priority = time_factor * 0.4 + success_factor * 0.3 + attempts_factor * 0.3
    priority = base_priority * last_attempt_factor

    # Scale priority based on active words
    # This helps prevent overwhelming the user with too many active words
    if active_words_count > 20:
        priority *= 20.0 / active_words_count

    return priority


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
