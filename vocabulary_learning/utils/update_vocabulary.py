"""Utility to update vocabulary entries and sync with Firebase."""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from vocabulary_learning.core.firebase_config import initialize_firebase


def update_vocabulary_entry(word_id: str, updates: Dict[str, Any]) -> bool:
    """Update a vocabulary entry and sync with Firebase.

    Args:
        word_id: The ID of the word to update (e.g., '000037')
        updates: Dictionary containing the fields to update and their new values
                (e.g., {'french': 'new translation'})

    Returns:
        bool: True if update was successful, False otherwise
    """
    console = Console()
    console.print(
        Panel.fit(
            f"[bold blue]Updating vocabulary entry {word_id}[/bold blue]",
            border_style="blue",
        )
    )

    # Get data directory
    data_dir = Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/data"))
    if not data_dir.exists():
        console.print(f"[red]Data directory not found at {data_dir}[/red]")
        return False

    # Load vocabulary data
    vocab_path = data_dir / "vocabulary.json"
    if not vocab_path.exists():
        console.print("[red]Error: vocabulary.json not found![/red]")
        return False

    try:
        # Read current vocabulary
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)

        # Check if word exists
        if word_id not in vocabulary:
            console.print(f"[red]Error: Word ID {word_id} not found in vocabulary[/red]")
            return False

        # Show current entry before update
        console.print("\n[bold]Current word entry:[/bold]")
        console.print_json(json.dumps(vocabulary[word_id], indent=2, ensure_ascii=False))

        # Update the word entry
        word_entry = vocabulary[word_id]
        for field, value in updates.items():
            if field in word_entry:
                word_entry[field] = value
            else:
                console.print(f"[yellow]Warning: Field '{field}' not found in word entry[/yellow]")

        # Save updated vocabulary locally
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(vocabulary, f, indent=2, ensure_ascii=False)
        console.print("[green]✓ Updated local vocabulary file[/green]")

        # Initialize Firebase and sync
        load_dotenv()
        _, vocabulary_ref = initialize_firebase(
            console=console,
            env_file=str(
                Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/.env"))
            ),
        )

        if vocabulary_ref:
            console.print("[dim]Syncing with Firebase...[/dim]", end="")
            vocabulary_ref.set(vocabulary)
            console.print("[green] ✓[/green]")
        else:
            console.print("[yellow]Warning: Could not initialize Firebase connection[/yellow]")
            console.print("[yellow]Changes saved locally only[/yellow]")

        # Show updated entry
        console.print("\n[bold]Updated word entry:[/bold]")
        console.print_json(json.dumps(vocabulary[word_id], indent=2, ensure_ascii=False))
        return True

    except Exception as e:
        console.print(f"[red]Error updating vocabulary: {str(e)}[/red]")
        return False


def main():
    """Execute the command-line interface for vocabulary updates."""
    parser = argparse.ArgumentParser(description="Update vocabulary entries")
    parser.add_argument("word_id", help="ID of the word to update (e.g., 000037)")

    # Add subparsers for different types of updates
    subparsers = parser.add_subparsers(dest="command", help="Type of update to perform")

    # French translation update
    french_parser = subparsers.add_parser("french", help="Update French translation")
    french_parser.add_argument("translation", help="New French translation")

    # Hiragana update
    hiragana_parser = subparsers.add_parser("hiragana", help="Update hiragana")
    hiragana_parser.add_argument("text", help="New hiragana text")

    # Kanji update
    kanji_parser = subparsers.add_parser("kanji", help="Update kanji")
    kanji_parser.add_argument("text", help="New kanji text")

    # Example sentence update
    example_parser = subparsers.add_parser("example", help="Update example sentence")
    example_parser.add_argument("sentence", help="New example sentence")

    # Parse arguments
    args = parser.parse_args()

    # Create updates dictionary based on command
    updates = {}
    if args.command == "french":
        updates["french"] = args.translation
    elif args.command == "hiragana":
        updates["hiragana"] = args.text
    elif args.command == "kanji":
        updates["kanji"] = args.text
    elif args.command == "example":
        updates["example_sentence"] = args.sentence
    else:
        parser.print_help()
        return

    # Update the vocabulary entry
    success = update_vocabulary_entry(args.word_id, updates)
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
