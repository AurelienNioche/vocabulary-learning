import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

def update_word_ids():
    console = Console()
    console.print("\n[bold blue]=== Updating Word IDs ===[/bold blue]")
    
    # Read existing vocabulary
    json_path = Path("data/vocabulary.json")
    if not json_path.exists():
        console.print("[red]Error: vocabulary.json not found[/red]")
        console.print("[yellow]Please make sure you have a vocabulary file in the data directory.[/yellow]")
        return
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        if not vocab_data:
            console.print("[red]Error: vocabulary.json is empty[/red]")
            return
        
        # Create backup before modifying
        backup_path = json_path.with_suffix('.json.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)
        console.print("[green]✓ Created backup of current vocabulary file[/green]")
        
        # Validate data structure
        for key, value in vocab_data.items():
            if not isinstance(value, dict) or not all(k in value for k in ['hiragana', 'kanji', 'french', 'example_sentence']):
                console.print(f"[red]Error: Invalid data structure found for entry {key}[/red]")
                console.print("[yellow]Restoring from backup...[/yellow]")
                backup_path.rename(json_path)
                return
        
        # Create new dictionary with updated IDs
        new_vocab_dict = {}
        for i, (_, word_data) in enumerate(sorted(vocab_data.items()), 1):
            new_key = f"word_{str(i).zfill(6)}"  # 6-digit padding
            new_vocab_dict[new_key] = word_data
        
        # Save updated vocabulary
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(new_vocab_dict, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]✓ Successfully updated {len(new_vocab_dict)} word IDs[/green]")
        console.print("[dim]A backup of the original file has been saved as vocabulary.json.bak[/dim]")
        
        if Confirm.ask("[yellow]Would you like to sync these changes to Firebase?[/yellow]"):
            # Import and run sync_to_firebase
            from sync_to_firebase import sync_to_firebase
            sync_to_firebase()
        
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format in vocabulary file[/red]")
    except Exception as e:
        console.print(f"[red]Error during ID update: {str(e)}[/red]")
        if backup_path.exists():
            console.print("[yellow]Restoring from backup...[/yellow]")
            backup_path.rename(json_path)
            console.print("[green]✓ Successfully restored from backup[/green]")

if __name__ == "__main__":
    update_word_ids() 