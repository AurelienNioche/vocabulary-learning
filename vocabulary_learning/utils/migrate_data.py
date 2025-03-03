"""Script to migrate data format and push to Firebase."""

import json
import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, db
from rich.console import Console


def migrate_data_format():
    """Migrate data format and push to Firebase."""
    console = Console()
    console.print("[bold blue]Starting data format migration...[/bold blue]")

    # Get data directory
    data_dir = Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/data"))
    if not data_dir.exists():
        console.print(f"[red]Data directory not found at {data_dir}[/red]")
        return

    # Initialize Firebase
    if not firebase_admin._apps:
        load_dotenv()
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")},
        )

    # Process progress data
    progress_file = data_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file, "r") as f:
            progress_data = json.load(f)

        # Convert progress data format
        new_progress_data = {}
        for word_id, word_data in progress_data.items():
            if word_id.startswith("word_"):
                new_id = word_id.split("word_")[1]  # Already in leading zeros format
                new_progress_data[new_id] = word_data
            else:
                new_progress_data[word_id] = word_data

        # Save locally
        with open(progress_file, "w") as f:
            json.dump(new_progress_data, f, indent=2)
        console.print(
            f"[green]✓ Updated local progress data ({len(new_progress_data)} records)[/green]"
        )

        # Push to Firebase
        progress_ref = db.reference("progress")
        progress_ref.set(new_progress_data)
        console.print("[green]✓ Pushed progress data to Firebase[/green]")

    # Process vocabulary data
    vocab_file = data_dir / "vocabulary.json"
    if vocab_file.exists():
        with open(vocab_file, "r") as f:
            vocab_data = json.load(f)

        # Convert vocabulary data format
        new_vocab_data = {}
        for word_id, word_data in vocab_data.items():
            if word_id.startswith("word_"):
                new_id = word_id.split("word_")[1]  # Already in leading zeros format
                new_vocab_data[new_id] = word_data
            else:
                new_vocab_data[word_id] = word_data

        # Save locally
        with open(vocab_file, "w") as f:
            json.dump(new_vocab_data, f, indent=2)
        console.print(
            f"[green]✓ Updated local vocabulary data ({len(new_vocab_data)} records)[/green]"
        )

        # Push to Firebase
        vocab_ref = db.reference("vocabulary")
        vocab_ref.set(new_vocab_data)
        console.print("[green]✓ Pushed vocabulary data to Firebase[/green]")

    console.print("\n[bold green]Migration complete![/bold green]")


if __name__ == "__main__":
    migrate_data_format()
