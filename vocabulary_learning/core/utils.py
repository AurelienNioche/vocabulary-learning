"""Utility functions for text processing and other helpers."""

import os
import sys
import unicodedata
from difflib import SequenceMatcher

from rich.console import Console


def normalize_french(text):
    """Remove accents and normalize French text."""
    # Convert to lowercase and strip
    text = text.lower().strip()
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    # Remove diacritics
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def is_minor_typo(str1, str2, threshold=0.85):
    """Check if two strings are similar enough to be considered a typo."""
    return SequenceMatcher(None, str1, str2).ratio() > threshold


def show_answer_feedback(console, answer, is_correct, message=None):
    """Show feedback for an answer with consistent formatting."""
    print("\033[A", end="")  # Move cursor up one line
    print("\033[2K", end="")  # Clear the line
    status = "[bold green]✓ Correct!" if is_correct else "[bold red]✗ Incorrect[/bold red]"
    console.print(f"Your answer: {answer}    {status}")
    if message:
        console.print(message)


def format_multiple_answers(answers):
    """Format multiple answers consistently with green highlighting."""
    return " / ".join(f"[green]{ans}[/green]" for ans in answers)


def update_progress_if_first_attempt(
    update_fn, word_id: str, success: bool, is_first_attempt: bool
):
    """Update progress if this is the first attempt.

    Updates the progress tracking data for a word, but only if this is the first attempt
    at answering it in the current session.

    Args:
        update_fn: Function to call to update progress
        word_id: The word ID (e.g., 'word_000001')
        success: Whether the attempt was successful
        is_first_attempt: Whether this is the first attempt
    """
    if is_first_attempt:
        update_fn(word_id, success)


def exit_with_save(save_progress_fn, console):
    """Exit the program after saving progress."""
    console.print("\n\n[dim]Saving progress...[/dim]")
    save_progress_fn()
    console.print("[bold green]Goodbye![/bold green]")
    sys.exit(0)


def signal_handler(signum, frame, save_progress_fn):
    """Handle Ctrl+C gracefully with the same behavior as :q"""
    console = Console()
    exit_with_save(save_progress_fn, console)


def format_time_interval(hours):
    """Format time interval in days, hours, and minutes.

    Formats a time interval given in hours into a human-readable string.
    Only shows the relevant units (e.g., only minutes if < 1h, only hours and minutes if < 1d).

    """
    if hours == 0:
        return "as soon as possible"

    # Convert to minutes for more precise comparison
    total_minutes = hours * 60

    if total_minutes < 1:
        return "less than 1 minute"

    # Round to nearest minute to avoid floating point imprecision
    total_minutes = round(total_minutes)
    days = total_minutes // (24 * 60)
    remaining_minutes = total_minutes % (24 * 60)
    hours = remaining_minutes // 60
    minutes = remaining_minutes % 60

    if days > 0:
        if hours > 0 or minutes > 0:
            if minutes > 0:
                return f"{days}d {hours}h {minutes}min"
            return f"{days}d {hours}h"
        return f"{days}d"
    elif hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}min"
        return f"{hours}h"
    else:
        return f"{minutes}min"


def get_data_dir() -> str:
    """Get the OS-specific data directory for storing application data.

    Returns:
        Path to the data directory
    """
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/VocabularyLearning")
    else:
        return os.path.expanduser("~/.local/share/vocabulary-learning")
