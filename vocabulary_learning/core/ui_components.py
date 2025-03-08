"""UI components for displaying information and statistics."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.table import Table

from vocabulary_learning.core.constants import (
    FAILURE_MARK,
    MAX_REVIEW_INTERVALS_HISTORY,
    SUCCESS_MARK,
)
from vocabulary_learning.core.text_processing import (
    format_datetime,
    format_time_interval,
)


def show_progress(vocabulary, progress, console):
    """Display progress statistics in a nice table format."""
    table = Table(title="Vocabulary Progress")
    table.add_column("Japanese", style="bold")
    table.add_column("Kanji", style="bold cyan")
    table.add_column("French", style="bold green")
    table.add_column("Status", style="bold", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Attempts", justify="right")
    table.add_column("Last Practice", justify="right")

    for i, row in vocabulary.iterrows():
        word_id = f"word_{str(i + 1).zfill(6)}"
        japanese = row["japanese"]
        kanji = row["kanji"] if pd.notna(row["kanji"]) else ""
        french = row["french"]
        stats = progress.get(
            word_id, {"attempts": 0, "successes": 0, "last_seen": "Never"}
        )

        attempts = stats["attempts"]
        success_rate = (stats["successes"] / attempts * 100) if attempts > 0 else 0

        # Determine status
        if attempts >= 10:
            if success_rate >= 80:
                status = "[green]Mastered[/green]"
            elif success_rate >= 60:
                status = "[yellow]Learning[/yellow]"
            else:
                status = "[red]Needs Work[/red]"
        else:
            status = f"[blue]{attempts}/10[/blue]"

        last_seen = stats["last_seen"]
        if last_seen != "Never":
            last_seen_date = datetime.fromisoformat(last_seen)
            days_ago = (datetime.now() - last_seen_date).days
            if days_ago == 0:
                last_seen = "Today"
            elif days_ago == 1:
                last_seen = "Yesterday"
            else:
                last_seen = f"{days_ago} days ago"

        table.add_row(
            japanese,
            kanji,
            french,
            status,
            f"{success_rate:.0f}%",
            str(attempts),
            last_seen,
        )

    console.print(table)


def show_word_statistics(word_pair, progress, console):
    """Display statistics for a specific word."""
    # Get word ID from the word pair
    word_id = None
    if hasattr(word_pair, "name") and word_pair.name is not None:
        word_id = f"word_{str(word_pair.name + 1).zfill(6)}"
    else:
        # For words without an index, try to find them in the progress data
        for progress_id, progress_data in progress.items():
            if progress_data.get("japanese") == word_pair["japanese"]:
                word_id = progress_id
                break

    table = Table(title=f"Statistics for {word_pair['japanese']}")
    table.add_column("Information", style="bold")
    table.add_column("Value", style="green")

    stats = progress.get(
        word_id,
        {"attempts": 0, "successes": 0, "last_seen": "Never", "review_intervals": []},
    )

    success_rate = (
        (stats["successes"] / stats["attempts"] * 100) if stats["attempts"] > 0 else 0
    )
    last_seen = stats["last_seen"]
    if last_seen != "Never":
        last_seen = format_datetime(last_seen)

    # Calculate average interval between reviews
    intervals = stats.get("review_intervals", [])[
        -MAX_REVIEW_INTERVALS_HISTORY:
    ]  # Only use last N intervals
    avg_interval = sum(intervals) / len(intervals) if intervals else 0

    table.add_row("Japanese", word_pair["japanese"])
    if pd.notna(word_pair["kanji"]) and word_pair["kanji"]:
        table.add_row("Kanji", word_pair["kanji"])
    table.add_row("French", word_pair["french"])
    table.add_row("Success Rate", f"{success_rate:.0f}%")
    table.add_row("Total Attempts", str(stats["attempts"]))
    table.add_row("Successful Attempts", str(stats["successes"]))
    table.add_row("Failed Attempts", str(stats["attempts"] - stats["successes"]))
    table.add_row("Last Practice", last_seen)
    if avg_interval > 0:
        table.add_row("Average Review Interval", format_time_interval(avg_interval))

    # Add attempt history if available
    if "attempt_history" in stats and stats["attempt_history"]:
        history = ""
        for attempt in stats["attempt_history"]:
            history += SUCCESS_MARK if attempt["success"] else FAILURE_MARK
        table.add_row("Attempt History", history)

    console.print(table)


def show_save_status(progress_file, progress, last_save_time, console):
    """Show the current save status and statistics."""
    table = Table(title="Save Status")
    table.add_column("Information", style="bold")
    table.add_column("Value", style="green")

    # Get save file info
    save_file = Path(progress_file)
    file_exists = save_file.exists()

    if file_exists:
        file_size = save_file.stat().st_size
        last_modified = datetime.fromtimestamp(save_file.stat().st_mtime)
        seconds_since_save = (datetime.now() - last_save_time).total_seconds()

        table.add_row("Auto-save Status", "Active (saves after each answer)")
        table.add_row("Last Save", f"{seconds_since_save:.1f} seconds ago")
        table.add_row("Save File", progress_file)
        table.add_row("File Size", f"{file_size / 1024:.1f} KB")
        table.add_row("Words Tracked", str(len(progress)))
        table.add_row("Last Modified", last_modified.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        table.add_row("Auto-save Status", "[red]No save file found[/red]")
        table.add_row("Save File", progress_file)
        table.add_row("Words Tracked", "0")

    console.print(table)


def show_help(vim_commands, console):
    """Display Vim-like commands help."""
    table = Table(title="Available Commands")
    table.add_column("Command", style="bold")
    table.add_column("Description", style="green")

    for cmd, desc in vim_commands.items():
        table.add_row(cmd, desc)

    console.print(table)
