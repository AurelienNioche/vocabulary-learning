"""Script to fix duplicate entries in vocabulary and progress data."""

import json
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def fix_duplicates():
    """Fix duplicate entries in vocabulary and progress data."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Fix Duplicate Entries[/bold blue]\n\n"
            "This will:\n"
            "1. Create a backup of current files\n"
            "2. Merge duplicate entries (keeping lower IDs)\n"
            "3. Update vocabulary and progress data\n"
            "4. Save fixed data",
            title="Duplicate Fix",
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
        # Create backups
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        vocab_backup = data_dir / f"vocabulary_backup_{timestamp}.json"
        progress_backup = data_dir / f"progress_backup_{timestamp}.json"

        with open(vocab_path, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)
        with open(progress_path, "r", encoding="utf-8") as f:
            progress = json.load(f)

        # Create backups
        with open(vocab_backup, "w", encoding="utf-8") as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=2)
        with open(progress_backup, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        console.print(f"[green]✓ Created backups with timestamp {timestamp}[/green]")

        # Find duplicates
        hiragana_map = {}
        kanji_map = {}
        french_map = {}
        duplicates = []

        for word_id, word_data in vocabulary.items():
            hiragana = word_data["hiragana"]
            kanji = word_data.get("kanji", "")
            french = word_data["french"]

            # Check hiragana duplicates
            if hiragana in hiragana_map:
                duplicates.append(
                    {
                        "type": "hiragana",
                        "value": hiragana,
                        "id1": hiragana_map[hiragana],
                        "id2": word_id,
                    }
                )
            else:
                hiragana_map[hiragana] = word_id

            # Check kanji duplicates (if not empty)
            if kanji and kanji in kanji_map:
                duplicates.append(
                    {
                        "type": "kanji",
                        "value": kanji,
                        "id1": kanji_map[kanji],
                        "id2": word_id,
                    }
                )
            elif kanji:
                kanji_map[kanji] = word_id

            # Check french duplicates
            if french in french_map:
                duplicates.append(
                    {
                        "type": "french",
                        "value": french,
                        "id1": french_map[french],
                        "id2": word_id,
                    }
                )
            else:
                french_map[french] = word_id

        # Process duplicates
        processed_pairs = set()
        fixed_vocabulary = vocabulary.copy()
        fixed_progress = progress.copy()

        for dup in duplicates:
            pair = tuple(sorted([dup["id1"], dup["id2"]]))
            if pair in processed_pairs:
                continue

            id1, id2 = pair
            processed_pairs.add(pair)

            # Keep the entry with the lower ID
            if id2 in fixed_vocabulary:
                del fixed_vocabulary[id2]

            # Merge progress data if it exists
            if id2 in fixed_progress:
                if id1 in fixed_progress:
                    # Merge progress data (keep the better stats)
                    prog1 = fixed_progress[id1]
                    prog2 = fixed_progress[id2]

                    # Keep the higher success rate
                    if (
                        prog2["successes"] / prog2["attempts"]
                        > prog1["successes"] / prog1["attempts"]
                    ):
                        fixed_progress[id1] = prog2
                else:
                    # If no progress for id1, use id2's progress
                    fixed_progress[id1] = fixed_progress[id2]

                # Remove the duplicate progress
                del fixed_progress[id2]

        # Save fixed data
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(fixed_vocabulary, f, ensure_ascii=False, indent=2)
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(fixed_progress, f, ensure_ascii=False, indent=2)

        console.print(
            f"[green]✓ Fixed {len(processed_pairs)} duplicate pairs[/green]\n"
            f"[green]✓ Saved updated vocabulary and progress data[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error fixing duplicates: {str(e)}[/red]")
        return


if __name__ == "__main__":
    fix_duplicates()
