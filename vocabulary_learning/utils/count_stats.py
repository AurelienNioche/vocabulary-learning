#!/usr/bin/env python3
"""Run the script to count and display vocabulary learning progress statistics."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pytz
from rich.console import Console
from rich.table import Table

from vocabulary_learning.core.constants import DECAY_RATE, FAILURE_MARK, SUCCESS_MARK
from vocabulary_learning.core.paths import get_progress_file_path
from vocabulary_learning.core.progress_tracking import (
    calculate_weighted_success_rate,
    get_utc_now,
    is_mastered,
)


def get_progress_file() -> str:
    """Get the path to the progress.json file.

    Returns
    -------
        String path to the progress file
    """
    # First check current directory for backward compatibility
    if Path("progress.json").exists():
        return "progress.json"

    # Then check the standard location
    path = get_progress_file_path()
    if path.exists():
        return str(path)

    raise FileNotFoundError("Could not find progress.json file")


def count_progress_stats(progress_file: str) -> dict:
    """Count statistics about words in progress.

    This function analyzes the progress.json file and returns statistics about:
    - Total number of words being tracked
    - Number of active (non-mastered) words
    - Number of mastered words

    Args:
        progress_file: Path to the progress.json file

    Returns
    -------
        Dictionary containing:
            - total_words: Total number of words being tracked
            - active_words: Number of words that have been started but not mastered
            - mastered_words: Number of words that meet mastery criteria
    """
    with open(progress_file, "r") as f:
        progress = json.load(f)

    active_count = 0
    mastered_count = 0
    total_words = len(progress)

    for word_id, word_data in progress.items():
        if word_data.get("attempts", 0) > 0:
            if is_mastered(word_data):
                mastered_count += 1
            else:
                active_count += 1

    return {
        "total_words": total_words,
        "active_words": active_count,
        "mastered_words": mastered_count,
    }


def display_stats(stats: dict, console: Console):
    """Display statistics in a nicely formatted table."""
    table = Table(title="Vocabulary Learning Progress")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Count", style="green")
    table.add_column("Details", style="dim")

    table.add_row(
        "Total Words", str(stats["total_words"]), "Total number of words being tracked"
    )
    table.add_row(
        "Active Words",
        str(stats["active_words"]),
        "Words that have been started but not yet mastered",
    )
    table.add_row(
        "Mastered Words",
        str(stats["mastered_words"]),
        "Words that meet mastery criteria (≥5 successes, ≥80% success rate)",
    )

    console.print(table)


def display_item_stats(progress_file: str, console: Console):
    """Display detailed statistics for each attempted word."""
    with open(progress_file, "r") as f:
        progress = json.load(f)

    # Create table
    table = Table(title="Word-by-Word Statistics")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Successes", justify="right", style="green")
    table.add_column("Attempts", justify="right", style="yellow")
    table.add_column("Raw Success Rate", justify="right", style="cyan")
    table.add_column("Weighted Success Rate", justify="right", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Attempt History", style="dim")

    # Filter and sort words that have been attempted
    attempted_words = {
        word_id: data
        for word_id, data in progress.items()
        if data.get("attempts", 0) > 0
    }
    sorted_words = sorted(attempted_words.items(), key=lambda x: x[0])

    # Get current time for weighted calculations
    now = get_utc_now()

    # Debug: Print first word's attempt history
    if sorted_words:
        word_id, word_data = sorted_words[0]
        console.print(f"\n[dim]Debug info for {word_id.replace('word_', '')}:[/dim]")
        console.print(f"[dim]Current time: {now.isoformat()}[/dim]")
        attempt_history = word_data.get("attempt_history", [])
        if attempt_history:
            console.print("[dim]Attempt history:[/dim]")
            for attempt in attempt_history:
                timestamp = datetime.fromisoformat(attempt["timestamp"])
                if timestamp.tzinfo is None:
                    timestamp = pytz.UTC.localize(timestamp)
                hours_ago = (now - timestamp).total_seconds() / 3600.0
                weight = 2.718 ** (-DECAY_RATE * hours_ago)
                console.print(
                    f"[dim]- {timestamp.isoformat()}: "
                    f"{'Success' if attempt['success'] else 'Failure'}, "
                    f"{hours_ago:.1f} hours ago, "
                    f"weight={weight:.3f}[/dim]"
                )
        else:
            console.print("[dim]No attempt history found[/dim]")

    # Add rows for each word
    for word_id, word_data in sorted_words:
        successes = word_data.get("successes", 0)
        attempts = word_data.get("attempts", 0)
        raw_rate = (successes / attempts * 100) if attempts > 0 else 0
        weighted_rate = (
            calculate_weighted_success_rate(word_data.get("attempt_history", []), now)
            * 100
        )
        status = (
            "[green]Mastered[/green]"
            if is_mastered(word_data)
            else "[yellow]Learning[/yellow]"
        )

        # Create attempt history string (✓ for success, ✗ for failure)
        attempt_history = word_data.get("attempt_history", [])
        history_str = "".join(
            SUCCESS_MARK if attempt["success"] else FAILURE_MARK
            for attempt in attempt_history
        )

        table.add_row(
            word_id.replace("word_", ""),  # Remove 'word_' prefix
            str(successes),
            str(attempts),
            f"{raw_rate:.1f}%",
            f"{weighted_rate:.1f}%",
            status,
            history_str,
        )

    console.print(table)


def main():
    """Display vocabulary learning progress statistics."""
    parser = argparse.ArgumentParser(
        description="Display vocabulary learning progress statistics"
    )
    parser.add_argument(
        "--progress-file",
        help="Path to progress.json file (optional, will try to find automatically if not provided)",
    )
    parser.add_argument(
        "--items",
        action="store_true",
        help="Show detailed statistics for each attempted word",
    )
    args = parser.parse_args()

    try:
        progress_file = args.progress_file or get_progress_file()
        console = Console()

        # Log the file path being used
        console.print(f"\n[dim]Using progress file: {progress_file}[/dim]\n")

        if args.items:
            display_item_stats(progress_file, console)
        else:
            stats = count_progress_stats(progress_file)
            display_stats(stats, console)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
