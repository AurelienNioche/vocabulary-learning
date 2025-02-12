"""File operations for loading and saving vocabulary and progress."""

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd


def load_vocabulary(vocab_file, vocab_ref, console):
    """Load vocabulary from JSON file."""
    try:
        with open(vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        if not vocab_data:
            vocabulary = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
            console.print("[yellow]No vocabulary data found[/yellow]")
            return vocabulary

        # Convert JSON data to DataFrame
        vocab_list = []
        for word_id, word_data in vocab_data.items():
            vocab_list.append(
                {
                    "japanese": word_data["hiragana"],
                    "kanji": word_data["kanji"],
                    "french": word_data["french"],
                    "example_sentence": word_data["example_sentence"],
                }
            )

        vocabulary = pd.DataFrame(vocab_list)
        # Clean whitespace from entries
        vocabulary = vocabulary.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        # Remove any empty rows
        vocabulary = vocabulary.dropna(subset=["japanese", "french"])
        console.print(f"[green]✓ Loaded {len(vocabulary)} words[/green]")

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
        return pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format in vocabulary file[/red]")
        return pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
    except Exception as e:
        console.print(f"[red]Error loading vocabulary: {str(e)}[/red]")
        return pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])


def load_progress(progress_file, progress_ref, console):
    """Load learning progress from Firebase or local JSON file."""
    if progress_ref is not None:
        try:
            # Try to load from Firebase
            progress = progress_ref.get() or {}
            return progress
        except Exception as e:
            console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Falling back to local file...[/yellow]")

    # Fallback to local file
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
            # Migrate old progress data to new format
            for word in progress:
                if "review_intervals" not in progress[word]:
                    progress[word]["review_intervals"] = []
                if "last_attempt_was_failure" not in progress[word]:
                    progress[word]["last_attempt_was_failure"] = False
            return progress
    return {}


def save_progress(progress, progress_file, progress_ref, console):
    """Save learning progress to Firebase and local backup."""
    # Always save to local file as backup
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    # Try to save to Firebase
    if progress_ref is not None:
        try:
            progress_ref.set(progress)
        except Exception as e:
            console.print(f"[yellow]Failed to save to Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Progress saved to local file only.[/yellow]")
