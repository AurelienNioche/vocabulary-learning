"""Script to sync local data to Firebase."""

import json
from pathlib import Path

from rich.console import Console

from vocabulary_learning.core.constants import MACOS_DATA_DIR
from vocabulary_learning.core.firebase_config import initialize_firebase


def sync_to_firebase():
    """Sync local data to Firebase."""
    console = Console()

    # Initialize Firebase
    progress_ref, vocab_ref = initialize_firebase(
        console=console, env_file=str(MACOS_DATA_DIR / ".env")
    )

    if not progress_ref or not vocab_ref:
        console.print("[red]Failed to initialize Firebase[/red]")
        return

    # Load local vocabulary
    vocab_file = MACOS_DATA_DIR / "data" / "vocabulary.json"
    progress_file = MACOS_DATA_DIR / "data" / "progress.json"

    try:
        with open(vocab_file, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)

        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)

        # Push to Firebase
        console.print("[dim]Syncing vocabulary to Firebase...[/dim]", end="")
        vocab_ref.set(vocabulary)
        console.print("[green] ✓[/green]")

        console.print("[dim]Syncing progress to Firebase...[/dim]", end="")
        progress_ref.set(progress)
        console.print("[green] ✓[/green]")

        console.print("[green]Successfully synced local data to Firebase![/green]")

    except Exception as e:
        console.print(f"[red]Error syncing data: {str(e)}[/red]")


if __name__ == "__main__":
    sync_to_firebase()
