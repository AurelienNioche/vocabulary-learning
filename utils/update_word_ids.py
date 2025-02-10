import json
from pathlib import Path
from rich.console import Console

def update_word_ids():
    console = Console()
    console.print("\n[bold blue]=== Updating Word IDs ===[/bold blue]")
    
    # Read existing vocabulary
    json_path = Path("data/vocabulary.json")
    if not json_path.exists():
        console.print("[red]Error: vocabulary.json not found[/red]")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    
    # Create new dictionary with updated IDs
    new_vocab_dict = {}
    for i, (_, word_data) in enumerate(sorted(vocab_data.items()), 1):
        new_key = f"word_{str(i).zfill(6)}"  # 6-digit padding
        new_vocab_dict[new_key] = word_data
    
    # Save updated vocabulary
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(new_vocab_dict, f, ensure_ascii=False, indent=2)
    
    console.print(f"[green]✓ Successfully updated {len(new_vocab_dict)} word IDs[/green]")

if __name__ == "__main__":
    update_word_ids() 