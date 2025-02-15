"""Vocabulary management functionality."""

import json
import os
from datetime import datetime
from typing import Any, Callable

import pandas as pd
from rich.console import Console
from rich.prompt import Confirm

from vocabulary_learning.core.file_operations import save_vocabulary


def add_vocabulary(
    vocab_file: str,
    vocabulary: pd.DataFrame,
    vocab_ref: Any,
    console: Console,
    load_vocabulary: Callable,
) -> None:
    """Add new vocabulary words.

    Args:
        vocab_file: Path to vocabulary file
        vocabulary: Current vocabulary DataFrame
        vocab_ref: Firebase reference for vocabulary
        console: Console for output
        load_vocabulary: Function to reload vocabulary
    """
    console.print("\nAdd New Vocabulary")
    console.print("Enter 'q' to return to menu")

    while True:
        # Get word details
        japanese = input("Japanese (hiragana): ").strip()
        if japanese.lower() == "q":
            break

        # Check for duplicates
        if any(vocabulary["japanese"].str.lower() == japanese.lower()):
            console.print("[red]This word already exists![/red]")
            continue

        kanji = input("Kanji (optional): ").strip()
        french = input("French: ").strip()
        example = input("Example sentence (optional): ").strip()

        # Load existing vocabulary
        try:
            with open(vocab_file, "r", encoding="utf-8") as f:
                vocab_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            vocab_data = {}

        # Convert old list format to dictionary if needed
        if isinstance(vocab_data, list):
            try:
                vocab_data = {
                    f"word_{str(i+1).zfill(6)}": {
                        "hiragana": (
                            word.get("japanese", word.get("hiragana", ""))
                            if isinstance(word, dict)
                            else ""
                        ),
                        "kanji": word.get("kanji", "") if isinstance(word, dict) else "",
                        "french": word.get("french", "") if isinstance(word, dict) else "",
                        "example_sentence": (
                            word.get("example_sentence", "") if isinstance(word, dict) else ""
                        ),
                    }
                    for i, word in enumerate(vocab_data)
                    if isinstance(word, dict)
                }
            except (AttributeError, TypeError):
                vocab_data = {}
        elif not isinstance(vocab_data, dict):
            vocab_data = {}

        # Generate new word ID
        next_id = 1
        while f"word_{str(next_id).zfill(6)}" in vocab_data:
            next_id += 1
        word_id = f"word_{str(next_id).zfill(6)}"

        # Create new word entry
        vocab_data[word_id] = {
            "hiragana": japanese,
            "kanji": kanji,
            "french": french,
            "example_sentence": example,
        }

        # Save to file
        with open(vocab_file, "w", encoding="utf-8") as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)
        console.print("Saving to local file... ", end="")
        console.print("✓", style="green")

        # Sync with Firebase
        if vocab_ref is not None:
            try:
                vocab_ref.set(vocab_data)
                console.print("Syncing with Firebase... ", end="")
                console.print("✓", style="green")
            except Exception as e:
                console.print(f"[red]Failed to sync with Firebase: {str(e)}[/red]")

        # Reload vocabulary
        load_vocabulary()

        console.print("✓ Word added successfully!", style="green")

        # Ask if user wants to add another word
        if not Confirm.ask("Add another word?"):
            break


def reset_progress(progress_file, progress_ref, progress, save_progress_fn, console):
    """Reset all learning progress."""
    if Confirm.ask("[red]Are you sure you want to reset all progress? This cannot be undone[/red]"):
        # Backup current progress
        if os.path.exists(progress_file):
            backup_file = f"{progress_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with (
                    open(progress_file, "r", encoding="utf-8") as src,
                    open(backup_file, "w", encoding="utf-8") as dst,
                ):
                    dst.write(src.read())
                console.print(f"[dim]Progress backed up to: {backup_file}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not create backup: {str(e)}[/yellow]")

        # Reset progress
        progress.clear()
        save_progress_fn()

        # Reset Firebase if available
        firebase_status = ""
        if progress_ref is not None:
            try:
                progress_ref.set({})
                firebase_status = " and Firebase"
            except Exception as e:
                firebase_status = f" (Firebase reset failed: {str(e)})"

        console.print(f"[green]Progress reset successfully{firebase_status}![/green]")
    else:
        console.print("[dim]Progress reset cancelled[/dim]")
