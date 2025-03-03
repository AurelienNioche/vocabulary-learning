"""Utilities for console output and UI feedback."""

import sys

from rich.console import Console


def show_answer_feedback(console: Console, answer: str, is_correct: bool, message=None):
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


def exit_with_save(save_progress_fn, console: Console):
    """Exit the program after saving progress."""
    console.print("\n\n[dim]Saving progress...[/dim]")
    save_progress_fn()
    console.print("[bold green]Goodbye![/bold green]")
    sys.exit(0)
