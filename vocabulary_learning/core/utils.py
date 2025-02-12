"""Utility functions for text processing and other helpers."""

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


def update_progress_if_first_attempt(update_fn, word, success, is_first_attempt):
    """Update progress if this is the first attempt."""
    if is_first_attempt:
        update_fn(word, success)


def exit_with_save(save_progress_fn, console=None):
    """Exit the application gracefully with saving progress."""
    if console is None:
        console = Console()
    console.print()  # Add empty line
    console.print("\n[yellow]Saving progress...[/yellow]", end="")
    save_progress_fn()
    console.print("[yellow] ✓ Done![/yellow]")
    console.print("[bold green]Goodbye![/bold green]")
    sys.exit(0)


def signal_handler(signum, frame, save_progress_fn):
    """Handle Ctrl+C gracefully with the same behavior as :q"""
    exit_with_save(save_progress_fn)
