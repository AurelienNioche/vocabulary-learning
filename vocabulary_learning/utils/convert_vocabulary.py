"""Script to convert vocabulary from array to object format."""

import json
import os
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def get_data_dir() -> str:
    """Get the OS-specific data directory for storing application data."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/VocabularyLearning")
    else:
        return os.path.expanduser("~/.local/share/vocabulary-learning")


def convert_vocabulary():
    """Convert vocabulary from array to object format."""
    console.print("\n=== Converting Vocabulary Format ===")

    # Read the source vocabulary file
    source_path = Path("vocabulary.json")
    if not source_path.exists():
        console.print("[red]Error: vocabulary.json not found![/red]")
        return

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            vocab_array = json.load(f)

        # Convert to object format
        vocab_dict = {}
        for i, word in enumerate(vocab_array, start=1):
            word_id = f"word_{str(i).zfill(6)}"
            vocab_dict[word_id] = {
                "hiragana": word.get("hiragana", ""),
                "kanji": word.get("kanji", ""),
                "french": word.get("french", ""),
                "example_sentence": word.get("example_sentence", ""),
            }

        # Ensure data directory exists
        data_dir = Path(get_data_dir()) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Save converted vocabulary
        output_path = data_dir / "vocabulary.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(vocab_dict, f, ensure_ascii=False, indent=2)

        console.print(
            f"[green]✓ Successfully converted {len(vocab_array)} words[/green]"
        )
        console.print(f"[dim]Saved to: {output_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during conversion: {str(e)}[/red]")


if __name__ == "__main__":
    convert_vocabulary()
