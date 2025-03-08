"""Script to find duplicate entries in vocabulary and progress data."""

import json
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def find_duplicates():
    """Find duplicate entries in vocabulary and progress data."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Find Duplicate Entries[/bold blue]\n\n"
            "This will:\n"
            "1. Load vocabulary and progress data\n"
            "2. Find entries with duplicate hiragana/kanji/french\n"
            "3. Show a report of duplicates",
            title="Duplicate Check",
            border_style="blue",
        )
    )

    # Get data directory
    data_dir = Path(
        os.path.expanduser("~/Library/Application Support/VocabularyLearning/data")
    )
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

        # Find duplicates in vocabulary
        hiragana_map = {}
        kanji_map = {}
        french_map = {}
        duplicates = []

        for word_id, word_data in vocabulary.items():
            hiragana = word_data["hiragana"]
            kanji = word_data["kanji"]
            french = word_data["french"]

            # Check hiragana duplicates
            if hiragana in hiragana_map:
                duplicates.append(
                    {
                        "type": "hiragana",
                        "value": hiragana,
                        "id1": hiragana_map[hiragana],
                        "id2": word_id,
                        "word1": vocabulary[hiragana_map[hiragana]],
                        "word2": word_data,
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
                        "word1": vocabulary[kanji_map[kanji]],
                        "word2": word_data,
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
                        "word1": vocabulary[french_map[french]],
                        "word2": word_data,
                    }
                )
            else:
                french_map[french] = word_id

        if duplicates:
            # Create a table to display duplicates
            table = Table(title="Duplicate Entries")
            table.add_column("Type", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("ID 1", style="green")
            table.add_column("ID 2", style="green")
            table.add_column("Details", style="yellow")

            for dup in duplicates:
                word1 = dup["word1"]
                word2 = dup["word2"]
                details = (
                    f"1: {word1['hiragana']} ({word1['kanji']}) = {word1['french']}\n"
                    f"2: {word2['hiragana']} ({word2['kanji']}) = {word2['french']}"
                )
                table.add_row(
                    dup["type"], dup["value"], dup["id1"], dup["id2"], details
                )

            console.print(table)
            console.print(
                f"\n[yellow]Found {len(duplicates)} duplicate entries[/yellow]"
            )

            # Check if these entries exist in progress data
            progress_conflicts = []
            for dup in duplicates:
                id1_progress = progress.get(dup["id1"])
                id2_progress = progress.get(dup["id2"])
                if id1_progress and id2_progress:
                    progress_conflicts.append((dup["id1"], dup["id2"]))

            if progress_conflicts:
                console.print(
                    "\n[red]Warning: The following duplicates have progress data:[/red]"
                )
                for id1, id2 in progress_conflicts:
                    console.print(f"[dim]- {id1} and {id2}[/dim]")
                console.print(
                    "\n[yellow]You should manually review these entries and decide which to keep.[/yellow]"
                )
        else:
            console.print("[green]✓ No duplicates found![/green]")

    except Exception as e:
        console.print(f"[red]Error checking for duplicates: {str(e)}[/red]")
        return


if __name__ == "__main__":
    find_duplicates()
