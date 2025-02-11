import pandas as pd
import json
from typing import Dict, Optional
from rich.console import Console
from rich.table import Table

class VocabularyManager:
    def __init__(self, vocab_file: str, firebase_ref=None):
        self.vocab_file = vocab_file
        self.firebase_ref = firebase_ref
        self.vocabulary = None
        self.console = Console()
        self.load_vocabulary()
        
        # Share vocabulary with progress manager
        if hasattr(self, 'progress_manager'):
            self.progress_manager.vocabulary = self.vocabulary

    def load_vocabulary(self) -> None:
        if self.firebase_ref:
            try:
                vocab_data = self.firebase_ref.get()
                if vocab_data:
                    self.vocabulary = pd.DataFrame(vocab_data.values())
                    return
            except Exception as e:
                self.console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")

        # Fallback to local file
        try:
            with open(self.vocab_file, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
                if isinstance(vocab_data, dict) and 'words' in vocab_data:
                    self.vocabulary = pd.DataFrame(vocab_data['words'])
                else:
                    self.vocabulary = pd.DataFrame(vocab_data.values())
        except FileNotFoundError:
            self.vocabulary = pd.DataFrame(columns=['hiragana', 'kanji', 'french', 'example_sentence'])

    def save_vocabulary(self) -> None:
        # Save to local file
        vocab_data = {'words': self.vocabulary.to_dict('records')}
        with open(self.vocab_file, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)

        # Try to save to Firebase
        if self.firebase_ref:
            try:
                vocab_dict = {
                    f"word_{i}": row.to_dict()
                    for i, row in self.vocabulary.iterrows()
                }
                self.firebase_ref.set(vocab_dict)
            except Exception as e:
                self.console.print(f"[yellow]Failed to sync to Firebase: {str(e)}[/yellow]")
