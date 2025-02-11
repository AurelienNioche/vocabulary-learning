import pandas as pd
import json
from pathlib import Path
from rich.console import Console

def convert_csv_to_json():
    console = Console()
    console.print("\n[bold blue]=== Converting CSV to JSON ===[/bold blue]")
    
    # Check if CSV file exists
    csv_path = Path("vocabulary.csv")
    if not csv_path.exists():
        console.print("[red]Error: vocabulary.csv not found![/red]")
        console.print("[yellow]Note: If you've already converted your vocabulary, you can use update_word_ids.py instead.[/yellow]")
        return
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Convert DataFrame to the required JSON format with zero-padded numbers
        vocab_dict = {
            f"word_{str(i+1).zfill(6)}": {  # Using zfill(6) for 6-digit padding
                "hiragana": row["japanese"],
                "kanji": row["kanji"] if pd.notna(row["kanji"]) else "",
                "french": row["french"],
                "example_sentence": row["example_sentence"] if pd.notna(row["example_sentence"]) else ""
            }
            for i, row in df.iterrows()
        }
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Save to JSON file
        json_path = data_dir / "vocabulary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]✓ Successfully converted {len(df)} words from CSV to JSON[/green]")
        console.print("[dim]The vocabulary.csv file can now be safely deleted.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error during conversion: {str(e)}[/red]")

if __name__ == "__main__":
    convert_csv_to_json() 