import pandas as pd
import json
from pathlib import Path

def convert_csv_to_json():
    # Read the CSV file
    csv_path = Path("vocabulary.csv")
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
    
    print(f"Successfully converted {len(df)} words from CSV to JSON")

if __name__ == "__main__":
    convert_csv_to_json() 