"""Add a new definition to a vocabulary entry."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from vocabulary_learning.core.firebase_config import initialize_firebase


def merge_translations(local_trans: str, firebase_trans: str) -> str:
    """Merge local and Firebase translations, removing duplicates.

    Args:
        local_trans: Local translations string (slash-separated)
        firebase_trans: Firebase translations string (slash-separated)

    Returns:
        Merged translations string
    """
    # Split and combine translations
    all_trans = set(local_trans.split("/") + firebase_trans.split("/"))
    # Remove empty strings and sort
    all_trans = sorted(t.strip() for t in all_trans if t.strip())
    return "/".join(all_trans)


def add_definition(word_id: str, definition: str) -> bool:
    """Add a new definition to a vocabulary entry.

    Args:
        word_id: The ID of the word to update (e.g., '000037')
        definition: The new definition to add
    """
    console = Console()

    # Get data directory
    data_dir = Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/data"))
    vocab_path = data_dir / "vocabulary.json"

    try:
        # Initialize Firebase first to check for remote changes
        load_dotenv()
        _, vocabulary_ref = initialize_firebase(
            console=console,
            env_file=str(
                Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/.env"))
            ),
        )

        if not vocabulary_ref:
            console.print("[yellow]Warning: Could not connect to Firebase[/yellow]")
            return False

        # Get Firebase data
        firebase_vocabulary = vocabulary_ref.get() or {}

        # Read local vocabulary
        with open(vocab_path, "r", encoding="utf-8") as f:
            local_vocabulary = json.load(f)

        # Check if word exists in either local or Firebase
        if word_id not in local_vocabulary and word_id not in firebase_vocabulary:
            console.print(f"[red]Error: Word ID {word_id} not found in local or Firebase[/red]")
            return False

        # Show current entries if they differ
        local_word = local_vocabulary.get(word_id, {})
        firebase_word = firebase_vocabulary.get(word_id, {})

        if local_word != firebase_word:
            console.print("\n[yellow]Warning: Local and Firebase entries differ[/yellow]")
            if local_word:
                console.print("\n[bold]Local entry:[/bold]")
                console.print_json(json.dumps(local_word, indent=2, ensure_ascii=False))
            if firebase_word:
                console.print("\n[bold]Firebase entry:[/bold]")
                console.print_json(json.dumps(firebase_word, indent=2, ensure_ascii=False))

        # Check if definition exists in Firebase before merging
        firebase_translations = firebase_word.get("french", "").split("/")
        if definition in firebase_translations:
            console.print(f"[yellow]Definition '{definition}' already exists in Firebase[/yellow]")
            return False

        # Check if definition exists in local before merging
        local_translations = local_word.get("french", "").split("/")
        if definition in local_translations:
            console.print(f"[yellow]Definition '{definition}' already exists locally[/yellow]")
            # Update Firebase with local version if it differs
            if local_word != firebase_word:
                vocabulary_ref.set(local_vocabulary)
                console.print("[green]✓ Updated Firebase to match local version[/green]")
            return False

        # Merge entries if they exist in both places
        if local_word and firebase_word:
            # Use the most complete entry as base
            word = firebase_word if len(firebase_word) >= len(local_word) else local_word
            # Add the new definition
            translations = word.get("french", "").split("/") if word.get("french") else []
            translations.append(definition)
            translations = sorted(t.strip() for t in translations if t.strip())
            word["french"] = "/".join(translations)
        else:
            # Use whichever entry exists
            word = local_word or firebase_word
            # Add the new definition
            translations = word.get("french", "").split("/") if word.get("french") else []
            translations.append(definition)
            translations = sorted(t.strip() for t in translations if t.strip())
            word["french"] = "/".join(translations)

        # Update both local and Firebase
        local_vocabulary[word_id] = word
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(local_vocabulary, f, indent=2, ensure_ascii=False)
        console.print("[green]✓ Updated local vocabulary file[/green]")

        vocabulary_ref.set(local_vocabulary)
        console.print("[green]✓ Updated Firebase[/green]")

        # Show updated entry
        console.print("\n[bold]Updated entry:[/bold]")
        console.print_json(json.dumps(word, indent=2, ensure_ascii=False))
        return True

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m vocabulary_learning.utils.add_definition WORD_ID DEFINITION")
        print("Example: python -m vocabulary_learning.utils.add_definition 000037 'avoir un lien'")
        sys.exit(1)

    word_id = sys.argv[1]
    definition = sys.argv[2]

    if not add_definition(word_id, definition):
        sys.exit(1)
