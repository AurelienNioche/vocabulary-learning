"""Utilities for handling system signals."""

from rich.console import Console


def signal_handler(signum, frame, save_progress_fn):
    """Handle Ctrl+C gracefully with the same behavior as :q"""
    console = Console()
    console.print("\n\n[dim]Saving progress...[/dim]")
    save_progress_fn()
    console.print("[bold green]Goodbye![/bold green]")
    import sys

    sys.exit(0)
