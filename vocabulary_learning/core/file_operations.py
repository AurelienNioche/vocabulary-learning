"""File operations for loading and saving vocabulary and progress."""

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd


def load_vocabulary(vocab_file, vocab_ref, console):
    """Load vocabulary from Firebase or local JSON file."""
    # First try to load from Firebase if available
    if vocab_ref is not None:
        try:
            console.print("[dim]Attempting to load vocabulary from Firebase...[/dim]")
            vocab_data = vocab_ref.get()
            if vocab_data:
                # Convert Firebase data to DataFrame
                if isinstance(vocab_data, list):
                    # Convert old list format to dictionary
                    vocab_data = {
                        f"word_{str(i + 1).zfill(6)}": {
                            "hiragana": word.get("japanese", word.get("hiragana", "")),
                            "kanji": word.get("kanji", ""),
                            "french": word.get("french", ""),
                            "example_sentence": word.get("example_sentence", ""),
                        }
                        for i, word in enumerate(vocab_data)
                    }
                vocabulary = pd.DataFrame(
                    [
                        {
                            "japanese": word["hiragana"],
                            "kanji": word["kanji"],
                            "french": word["french"],
                            "example_sentence": word["example_sentence"],
                            "word_id": word_id,
                        }
                        for word_id, word in vocab_data.items()
                    ]
                )
                # Clean whitespace from entries
                vocabulary = vocabulary.apply(
                    lambda x: x.str.strip() if x.dtype == "object" else x
                )
                # Remove any empty rows
                vocabulary = vocabulary.dropna(subset=["japanese", "french"])
                console.print(
                    f"[green]✓ Loaded {len(vocabulary)} words from Firebase[/green]"
                )
                return vocabulary
            else:
                console.print("[yellow]No vocabulary data found in Firebase[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Falling back to local file...[/yellow]")

    # Fallback to local file
    try:
        console.print("[dim]Loading vocabulary from local file...[/dim]")
        with open(vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        if not vocab_data:
            vocabulary = pd.DataFrame(
                columns=["japanese", "kanji", "french", "example_sentence", "word_id"]
            )
            console.print("[yellow]No vocabulary data found in local file[/yellow]")
            return vocabulary

        # Convert JSON data to DataFrame
        if isinstance(vocab_data, list):
            # Convert old list format to dictionary
            vocab_data = {
                f"word_{str(i + 1).zfill(6)}": {
                    "hiragana": word.get("japanese", word.get("hiragana", "")),
                    "kanji": word.get("kanji", ""),
                    "french": word.get("french", ""),
                    "example_sentence": word.get("example_sentence", ""),
                }
                for i, word in enumerate(vocab_data)
            }

        vocabulary = pd.DataFrame(
            [
                {
                    "japanese": word["hiragana"],
                    "kanji": word["kanji"],
                    "french": word["french"],
                    "example_sentence": word["example_sentence"],
                    "word_id": word_id,
                }
                for word_id, word in vocab_data.items()
            ]
        )
        # Clean whitespace from entries
        vocabulary = vocabulary.apply(
            lambda x: x.str.strip() if x.dtype == "object" else x
        )
        # Remove any empty rows
        vocabulary = vocabulary.dropna(subset=["japanese", "french"])
        console.print(
            f"[green]✓ Loaded {len(vocabulary)} words from local file[/green]"
        )

        # Show last progress update time if progress file exists
        progress_file = str(Path(vocab_file).parent / "progress.json")
        if os.path.exists(progress_file):
            last_modified = datetime.fromtimestamp(os.path.getmtime(progress_file))
            time_diff = datetime.now() - last_modified
            if time_diff.days > 0:
                time_str = f"{time_diff.days} days ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hours ago"
            else:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minutes ago"
            console.print(f"[dim]Last progress update: {time_str}[/dim]")

        return vocabulary

    except FileNotFoundError:
        console.print("[yellow]No vocabulary file found[/yellow]")
        return pd.DataFrame(
            columns=["japanese", "kanji", "french", "example_sentence", "word_id"]
        )
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format in vocabulary file[/red]")
        return pd.DataFrame(
            columns=["japanese", "kanji", "french", "example_sentence", "word_id"]
        )
    except Exception as e:
        console.print(f"[red]Error loading vocabulary: {str(e)}[/red]")
        return pd.DataFrame(
            columns=["japanese", "kanji", "french", "example_sentence", "word_id"]
        )


def load_progress(progress_file, progress_ref, console):
    """Load learning progress from Firebase or local JSON file."""
    if progress_ref is not None:
        try:
            # Try to load from Firebase
            console.print("[dim]Attempting to load progress from Firebase...[/dim]")
            progress = progress_ref.get() or {}
            if progress:
                console.print(
                    f"[green]✓ Loaded progress for {len(progress)} words from Firebase[/green]"
                )
            else:
                console.print("[yellow]No progress data found in Firebase[/yellow]")
            return progress
        except Exception as e:
            console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Falling back to local file...[/yellow]")

    # Fallback to local file
    try:
        console.print("[dim]Loading progress from local file...[/dim]")
        if os.path.exists(progress_file):
            with open(progress_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:  # Handle empty file
                    console.print(
                        "[yellow]Empty progress file, starting fresh[/yellow]"
                    )
                    return {}
                progress = json.loads(content)
                # Migrate old progress data to new format
                for word in progress:
                    if "review_intervals" not in progress[word]:
                        progress[word]["review_intervals"] = []
                    if "last_attempt_was_failure" not in progress[word]:
                        progress[word]["last_attempt_was_failure"] = False
                console.print(
                    f"[green]✓ Loaded progress for {len(progress)} words from local file[/green]"
                )
                return progress
        else:
            console.print("[yellow]No progress file found, starting fresh[/yellow]")
            return {}
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format in progress file[/red]")
        return {}
    except Exception as e:
        console.print(f"[red]Error loading progress: {str(e)}[/red]")
        return {}


def save_progress(progress, progress_file, progress_ref, console):
    """Save learning progress to Firebase and local backup."""
    # Always save to local file as backup
    console.print("[dim]Saving to local file...[/dim]", end="")
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    console.print("[dim] ✓[/dim]")

    # Try to save to Firebase
    if progress_ref is not None:
        try:
            console.print("[dim]Syncing with Firebase...[/dim]", end="")
            progress_ref.set(progress)
            console.print("[dim] ✓[/dim]")
        except Exception as e:
            console.print(f"[yellow]Failed to sync with Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Progress saved to local file only.[/yellow]")


def save_vocabulary(vocabulary, vocab_file, vocab_ref, console):
    """Save vocabulary to Firebase and local backup."""
    # Convert DataFrame to dictionary format
    vocab_dict = {}
    for i, row in vocabulary.iterrows():
        word_id = f"word_{str(i + 1).zfill(6)}"
        vocab_dict[word_id] = {
            "hiragana": row["japanese"],
            "kanji": row["kanji"] if pd.notna(row["kanji"]) else "",
            "french": row["french"],
            "example_sentence": (
                row["example_sentence"] if pd.notna(row["example_sentence"]) else ""
            ),
        }

    # Always save to local file as backup
    console.print("[dim]Saving to local file...[/dim]", end="")
    with open(vocab_file, "w", encoding="utf-8") as f:
        json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
    console.print("[dim] ✓[/dim]")

    # Try to save to Firebase
    if vocab_ref is not None:
        try:
            console.print("[dim]Syncing with Firebase...[/dim]", end="")
            vocab_ref.set(vocab_dict)
            console.print("[dim] ✓[/dim]")
        except Exception as e:
            console.print(f"[yellow]Failed to sync with Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Vocabulary saved to local file only.[/yellow]")
