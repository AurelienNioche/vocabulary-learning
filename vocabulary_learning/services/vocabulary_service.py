"""Service layer for vocabulary management."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from firebase_admin import db
from rich.console import Console

from vocabulary_learning.core.vocabulary import format_word_entry, validate_word_entry


class VocabularyService:
    def __init__(
        self,
        vocabulary_file: str,
        vocabulary_ref: Optional[db.Reference] = None,
        console: Optional[Console] = None,
    ):
        """Initialize vocabulary service.

        Args:
            vocabulary_file: Path to vocabulary JSON file
            vocabulary_ref: Firebase reference for vocabulary
            console: Rich console for output (optional)
        """
        self.vocabulary_file = vocabulary_file
        self.vocabulary_ref = vocabulary_ref
        self.console = console or Console()

        # Ensure data directory exists
        data_dir = Path(vocabulary_file).parent
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load initial vocabulary
        self.vocabulary = self._load_vocabulary()

    def _load_vocabulary(self) -> Dict:
        """Load vocabulary from Firebase or local JSON file."""
        if self.vocabulary_ref is not None:
            try:
                # Try to load from Firebase
                vocabulary = self.vocabulary_ref.get() or {}
                return vocabulary
            except Exception as e:
                self.console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Falling back to local file...[/yellow]")

        # Fallback to local file
        if Path(self.vocabulary_file).exists():
            with open(self.vocabulary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_vocabulary(self):
        """Save vocabulary to Firebase and local backup."""
        # Always save to local file as backup
        with open(self.vocabulary_file, "w", encoding="utf-8") as f:
            json.dump(self.vocabulary, f, ensure_ascii=False, indent=2)

        # Try to save to Firebase
        if self.vocabulary_ref is not None:
            try:
                self.vocabulary_ref.set(self.vocabulary)
            except Exception as e:
                self.console.print(f"[yellow]Failed to save to Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Vocabulary saved to local file only.[/yellow]")

    def add_word(
        self,
        word: str,
        translations: List[str],
        example_sentences: Optional[List[Tuple[str, str]]] = None,
    ) -> bool:
        """Add a new word to the vocabulary.

        Args:
            word: Japanese word to add
            translations: List of French translations
            example_sentences: Optional list of (Japanese, French) example sentence pairs

        Returns:
            bool: True if word was added successfully
        """
        # Format and validate the word entry
        word_entry = format_word_entry(word, translations, example_sentences or [])
        if not validate_word_entry(word_entry):
            self.console.print("[red]Invalid word entry format[/red]")
            return False

        # Add or update the word
        self.vocabulary[word] = word_entry
        self.save_vocabulary()
        return True

    def get_word(self, word_id: str) -> Optional[Dict]:
        """Get a word's entry from the vocabulary.

        Args:
            word_id: The word ID (e.g., 'word_000001')

        Returns:
            Dictionary containing word details including hiragana
        """
        entry = self.vocabulary.get(word_id)
        if entry:
            return {
                "hiragana": entry.get("hiragana", ""),
                "kanji": entry.get("kanji", ""),
                "translations": entry.get("translations", []),
                "example_sentences": entry.get("example_sentences", []),
            }
        return None

    def get_all_words(self) -> List[str]:
        """Get list of all words in vocabulary.

        Returns:
            List of word IDs
        """
        return list(self.vocabulary.keys())

    def get_word_details(self, word_id: str) -> Optional[Dict]:
        """Get complete details for a word.

        Args:
            word_id: The word ID (e.g., 'word_000001')

        Returns:
            Complete word entry with all details
        """
        return self.vocabulary.get(word_id)

    def delete_word(self, word: str) -> bool:
        """Delete a word from the vocabulary.

        Returns:
            bool: True if word was deleted successfully
        """
        if word in self.vocabulary:
            del self.vocabulary[word]
            self.save_vocabulary()
            return True
        return False

    def update_word(
        self,
        word: str,
        translations: Optional[List[str]] = None,
        example_sentences: Optional[List[Tuple[str, str]]] = None,
    ) -> bool:
        """Update an existing word's translations or example sentences.

        Args:
            word: Word to update
            translations: New list of translations (if None, keep existing)
            example_sentences: New list of example sentences (if None, keep existing)

        Returns:
            bool: True if word was updated successfully
        """
        if word not in self.vocabulary:
            self.console.print(f"[red]Word '{word}' not found in vocabulary[/red]")
            return False

        current_entry = self.vocabulary[word]

        # Update translations if provided
        if translations is not None:
            current_entry["translations"] = translations

        # Update example sentences if provided
        if example_sentences is not None:
            current_entry["example_sentences"] = [
                {"jp": jp, "fr": fr} for jp, fr in example_sentences
            ]

        # Validate the updated entry
        if not validate_word_entry(current_entry):
            self.console.print("[red]Invalid word entry format after update[/red]")
            return False

        self.vocabulary[word] = current_entry
        self.save_vocabulary()
        return True

    def search_words(self, query: str) -> List[str]:
        """Search for words containing the query string.

        Args:
            query: Search string

        Returns:
            List of matching words
        """
        query = query.lower()
        matches = []

        for word, entry in self.vocabulary.items():
            # Check Japanese word
            if query in word.lower():
                matches.append(word)
                continue

            # Check translations
            if any(query in trans.lower() for trans in entry["translations"]):
                matches.append(word)
                continue

            # Check example sentences
            if any(
                query in sentence["jp"].lower() or query in sentence["fr"].lower()
                for sentence in entry["example_sentences"]
            ):
                matches.append(word)

        return matches
