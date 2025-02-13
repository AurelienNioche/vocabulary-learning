"""Vocabulary management functionality."""

import json
import os
from datetime import datetime

from rich.prompt import Confirm

from vocabulary_learning.core.file_operations import save_vocabulary


def add_vocabulary(vocab_file, vocabulary, vocab_ref, console, load_vocabulary_fn):
    """Add new vocabulary interactively."""
    print("\nAdd New Vocabulary")
    print("Enter 'q' to return to menu")

    while True:
        # Get Japanese word
        japanese = input("\nEnter Japanese word (hiragana): ").strip()
        if japanese.lower() == "q":
            break

        # Get kanji (optional)
        kanji = input("Enter kanji (optional): ").strip()
        if kanji.lower() == "q":
            break

        # Get French translation
        french = input("Enter French translation: ").strip()
        if french.lower() == "q":
            break

        # Get example sentence (optional)
        example = input("Enter example sentence (optional): ").strip()
        if example.lower() == "q":
            break

        # Validate input
        if not japanese or not french:
            console.print("[red]Japanese word and French translation are required![/red]")
            continue

        # Check for duplicates
        if any(vocabulary["japanese"].str.lower() == japanese.lower()):
            console.print("[red]This word already exists![/red]")
            continue

        try:
            # Add new word to vocabulary DataFrame
            new_word = {
                "japanese": japanese,
                "kanji": kanji if kanji else "",
                "french": french,
                "example_sentence": example if example else "",
            }
            vocabulary.loc[len(vocabulary)] = new_word

            # Save updated vocabulary
            save_vocabulary(vocabulary, vocab_file, vocab_ref, console)
            console.print("[green]✓ Word added successfully![/green]")

        except Exception as e:
            console.print(f"[red]Error adding word: {str(e)}[/red]")
            continue

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
