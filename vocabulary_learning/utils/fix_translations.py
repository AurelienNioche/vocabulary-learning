"""Script to fix noun translations in vocabulary."""

import json
import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def fix_translations():
    """Fix noun translations in vocabulary (e.g., 'échanger' -> 'échange')."""
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

    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)

        # Create backup
        backup_path = vocab_path.with_suffix(".json.bak")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=2)

        # Translations to fix
        translations_map = {
            "échanger": "échange",
            # Add more verb -> noun mappings here
        }

        # Fix translations
        changes_made = False
        for word_id, word_data in vocabulary.items():
            french = word_data.get("french", "")
            if french in translations_map:
                word_data["french"] = translations_map[french]
                console.print(
                    f"[yellow]Fixed translation for {word_data['hiragana']}: "
                    f"{french} -> {translations_map[french]}[/yellow]"
                )
                changes_made = True

        if changes_made:
            if Confirm.ask("[yellow]Would you like to save these changes?[/yellow]"):
                # Save changes
                with open(vocab_path, "w", encoding="utf-8") as f:
                    json.dump(vocabulary, f, ensure_ascii=False, indent=2)
                console.print("[green]✓ Changes saved successfully[/green]")
                console.print(
                    "[dim]A backup of the original file has been saved as vocabulary.json.bak[/dim]"
                )

                if Confirm.ask(
                    "[yellow]Would you like to sync these changes to Firebase?[/yellow]"
                ):
                    from vocabulary_learning.utils.sync_to_firebase import sync_to_firebase

                    sync_to_firebase()
            else:
                console.print("[yellow]Changes discarded[/yellow]")
        else:
            console.print("[green]No translations needed fixing[/green]")

    except Exception as e:
        console.print(f"[red]Error fixing translations: {str(e)}[/red]")
        if backup_path.exists():
            console.print("[yellow]Restoring from backup...[/yellow]")
            backup_path.rename(vocab_path)
            console.print("[green]✓ Successfully restored from backup[/green]")


if __name__ == "__main__":
    fix_translations()
