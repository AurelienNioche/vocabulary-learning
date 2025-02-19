"""Script to sync local data with Firebase."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from vocabulary_learning.core.firebase_config import initialize_firebase


def sync_to_firebase():
    """Sync local vocabulary and progress data with Firebase."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Firebase Sync[/bold blue]\n\n"
            "This will:\n"
            "1. Load local vocabulary and progress data\n"
            "2. Push data to Firebase\n"
            "3. Verify the sync",
            title="Firebase Sync",
            border_style="blue",
        )
    )

    # Get data directory
    data_dir = Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/data"))
    if not data_dir.exists():
        console.print(f"[red]Data directory not found at {data_dir}[/red]")
        return

    # Load vocabulary data
    vocab_path = data_dir / "vocabulary.json"
    if not vocab_path.exists():
        console.print("[red]Error: vocabulary.json not found![/red]")
        return

    # Load progress data
    progress_path = data_dir / "progress.json"
    if not progress_path.exists():
        console.print("[red]Error: progress.json not found![/red]")
        return

    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)
        with open(progress_path, "r", encoding="utf-8") as f:
            progress = json.load(f)

        # Initialize Firebase
        load_dotenv()
        progress_ref, vocabulary_ref = initialize_firebase(
            console=console,
            env_file=str(
                Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/.env"))
            ),
        )

        if not progress_ref or not vocabulary_ref:
            console.print("[red]Failed to initialize Firebase connection[/red]")
            return

        # Push data to Firebase
        console.print("[dim]Pushing vocabulary data...[/dim]", end="")
        vocabulary_ref.set(vocabulary)
        console.print("[green] ✓[/green]")

        console.print("[dim]Pushing progress data...[/dim]", end="")
        progress_ref.set(progress)
        console.print("[green] ✓[/green]")

        console.print("\n[green]✓ Successfully synced data with Firebase[/green]")

    except Exception as e:
        console.print(f"[red]Error syncing with Firebase: {str(e)}[/red]")
        return


if __name__ == "__main__":
    sync_to_firebase()
