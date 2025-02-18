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
    vocabulary: pd.DataFrame,
    vocab_file: str,
    vocab_ref: Any,
    console: Console,
    load_vocabulary: Callable,
    japanese_converter: Any = None,
    vim_commands: dict = None,
) -> None:
    """Add new vocabulary words.

    Args:
        vocabulary: Current vocabulary DataFrame
        vocab_file: Path to vocabulary file
        vocab_ref: Firebase reference for vocabulary
        console: Console for output
        load_vocabulary: Function to reload vocabulary
        japanese_converter: Optional JapaneseTextConverter instance for text conversion
        vim_commands: Dictionary of available Vim-like commands
    """
    console.print("\n[bold blue]Add New Vocabulary[/bold blue]")
    console.print()  # Add empty line
    console.print("[dim]Available commands:[/dim]")
    console.print("[blue]:m[/blue] menu • [blue]:q[/blue] quit")
    console.print()  # Add empty line

    while True:
        # Get word details
        japanese = input("Japanese (hiragana): ").strip()
        if japanese.lower() == ":m":
            break
        elif japanese.lower() == ":q":
            raise SystemExit
        elif not japanese:  # Skip empty input
            continue

        # Convert input to hiragana if converter is available and input is not a command
        if japanese_converter and not japanese.startswith(":"):
            try:
                japanese = japanese_converter.to_hiragana(japanese)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to convert text: {str(e)}[/yellow]")

        # Check for duplicates
        if not vocabulary.empty and any(vocabulary.japanese.str.lower() == japanese.lower()):
            console.print("[red]This word already exists![/red]")
            continue

        kanji = input("Kanji (optional): ").strip()
        french = input("French: ").strip()
        if not french:  # Skip if French translation is empty
            console.print("[red]French translation is required![/red]")
            continue

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
        console.print("[dim]Saving to local file... ✓[/dim]")

        # Sync with Firebase
        if vocab_ref is not None:
            try:
                vocab_ref.set(vocab_data)
                console.print("[dim]Syncing with Firebase... ✓[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to sync with Firebase: {str(e)}[/red]")

        # Reload vocabulary
        try:
            # Call load_vocabulary with the vocab_file and vocab_ref
            vocabulary = load_vocabulary(vocab_file, vocab_ref, console)
            if vocabulary is not None:
                console.print("[dim]Vocabulary reloaded successfully[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to reload vocabulary: {str(e)}[/yellow]")

        console.print("[green]✓ Word added successfully![/green]")

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
