"""Progress tracking functionality for vocabulary learning."""

import random
from datetime import datetime


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


def calculate_priority(word_data, active_words_count):
    """Calculate priority score for a word based on SuperMemo 2 algorithm."""
    MAX_ACTIVE_WORDS = 8  # Maximum number of words to learn at once

    # If this is a new word, check if we're already at max active words
    if word_data is None:
        if active_words_count >= MAX_ACTIVE_WORDS:
            return 0.0  # Don't introduce new words yet
        return 1.0  # Highest priority for new words if under the limit

    # Get basic stats
    successes = word_data.get("successes", 0)
    attempts = word_data.get("attempts", 0)
    interval = word_data.get("interval", 4)  # Default to 4 hours if not set
    last_seen = datetime.fromisoformat(word_data.get("last_seen", datetime.now().isoformat()))
    hours_since_last = (datetime.now() - last_seen).total_seconds() / 3600.0

    # Calculate success rate
    success_rate = (successes / max(attempts, 1)) * 100

    # If the word was last seen too recently, give it very low priority
    if hours_since_last < interval:
        return 0.01  # Too soon to review

    # Calculate how overdue the word is
    overdue_factor = max(0, (hours_since_last - interval) / interval)

    # Cap the overdue factor to avoid extremely high priorities for long-forgotten words
    overdue_factor = min(overdue_factor, 2.0)

    # Recent failure bonus
    failure_bonus = 0.3 if word_data.get("last_attempt_was_failure", False) else 0.0

    # Combine factors with weights
    priority = (
        (1 - success_rate / 100) * 0.4
        + overdue_factor * 0.4  # Success rate component
        + failure_bonus  # Overdue component
        + random.uniform(0, 0.1)  # Failure bonus  # Small random factor
    )

    # If we're at the max active words limit, only allow review of existing active words
    if active_words_count >= MAX_ACTIVE_WORDS and attempts < 1:
        return 0.0

    return priority


def count_active_learning_words(progress):
    """Count how many words are currently being actively learned (success rate < 80%)."""
    active_count = 0
    for _, data in progress.items():
        attempts = data.get("attempts", 0)
        if attempts > 0:  # Word has been seen at least once
            successes = data.get("successes", 0)
            success_rate = (successes / attempts) * 100
            if success_rate < 80:  # Not yet mastered
                active_count += 1
    return active_count
