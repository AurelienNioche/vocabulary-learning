"""Vocabulary management functionality."""

import os
import json
from rich.prompt import Confirm

def add_vocabulary(vocab_file, vocabulary, vocab_ref, console, load_vocabulary_fn):
    """Add new vocabulary interactively."""
    print("\nAdd New Vocabulary")
    print("Enter 'q' to return to menu")
    
    while True:
        # Get Japanese word
        japanese = input("\nEnter Japanese word (hiragana): ").strip()
        if japanese.lower() == 'q':
            break
        
        # Get kanji (optional)
        kanji = input("Enter kanji (optional): ").strip()
        if kanji.lower() == 'q':
            break
        
        # Get French translation
        french = input("Enter French translation: ").strip()
        if french.lower() == 'q':
            break
        
        # Get example sentence (optional)
        example = input("Enter example sentence (optional): ").strip()
        if example.lower() == 'q':
            break
        
        # Validate input
        if not japanese or not french:
            console.print("[red]Japanese word and French translation are required![/red]")
            continue
        
        # Check for duplicates
        if any(vocabulary['japanese'].str.lower() == japanese.lower()):
            console.print("[red]This word already exists![/red]")
            continue
        
        try:
            # Get the next word ID
            next_id = 1
            if os.path.exists(vocab_file):
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    vocab_data = json.load(f)
                    if vocab_data:
                        next_id = max(int(word_id.split('_')[1]) for word_id in vocab_data.keys()) + 1
            else:
                vocab_data = {}
            
            # Create new word entry
            new_word = {
                f"word_{str(next_id).zfill(6)}": {
                    "hiragana": japanese,
                    "kanji": kanji if kanji else "",
                    "french": french,
                    "example_sentence": example if example else ""
                }
            }
            
            # Update vocabulary data
            vocab_data.update(new_word)
            
            # Save to JSON file
            with open(vocab_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            
            # Update DataFrame
            load_vocabulary_fn()
            
            # Sync to Firebase if available
            if vocab_ref is not None:
                try:
                    vocab_ref.set(vocab_data)
                    console.print("[green]✓ Word added and synced to Firebase![/green]")
                except Exception as e:
                    console.print(f"[yellow]Word added locally but failed to sync to Firebase: {str(e)}[/yellow]")
            else:
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
                with open(progress_file, 'r', encoding='utf-8') as src, \
                     open(backup_file, 'w', encoding='utf-8') as dst:
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