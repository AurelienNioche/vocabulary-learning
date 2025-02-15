"""Service layer for practice sessions and word selection."""

import random
from typing import Dict, List, Optional, Tuple

from rich.console import Console

from vocabulary_learning.core.progress_tracking import is_mastered
from vocabulary_learning.services.progress_service import ProgressService
from vocabulary_learning.services.vocabulary_service import VocabularyService


class PracticeService:
    def __init__(
        self,
        vocabulary_service: VocabularyService,
        progress_service: ProgressService,
        console: Optional[Console] = None,
    ):
        """Initialize practice service.

        Args:
            vocabulary_service: VocabularyService instance
            progress_service: ProgressService instance
            console: Rich console for output (optional)
        """
        self.vocabulary_service = vocabulary_service
        self.progress_service = progress_service
        self.console = console or Console()

    def select_practice_words(self, num_words: int = 10) -> List[str]:
        """Select words for practice based on priority.

        Args:
            num_words: Number of words to select

        Returns:
            List of selected words
        """
        all_words = self.vocabulary_service.get_all_words()
        if not all_words:
            return []

        # Get active words count for priority calculation
        active_words_count = self.progress_service.count_active_words()

        # Calculate priority for each word
        word_priorities = [
            (word, self.progress_service.get_word_priority(word, active_words_count))
            for word in all_words
        ]

        # Sort by priority (higher priority first)
        word_priorities.sort(key=lambda x: x[1], reverse=True)

        # Select top N words with some randomization
        selected_words = []
        top_words = word_priorities[: min(num_words * 2, len(word_priorities))]

        # Always include some of the highest priority words
        num_guaranteed = max(1, num_words // 3)
        selected_words.extend(word[0] for word in top_words[:num_guaranteed])

        # Randomly select remaining words from top words, weighted by priority
        remaining_words = top_words[num_guaranteed:]
        if remaining_words:
            weights = [word[1] for word in remaining_words]
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
                num_remaining = min(num_words - len(selected_words), len(remaining_words))
                selected_remaining = random.choices(
                    [word[0] for word in remaining_words],
                    weights=weights,
                    k=num_remaining,
                )
                selected_words.extend(selected_remaining)

        # Shuffle the final selection
        random.shuffle(selected_words)
        return selected_words

    def get_word_details(self, word_id: str) -> Optional[Dict]:
        """Get combined vocabulary and progress details for a word.

        Args:
            word_id: The word ID (e.g., 'word_000001')

        Returns:
            Dictionary with word details and progress
        """
        vocab_entry = self.vocabulary_service.get_word(word_id)
        if not vocab_entry:
            return None

        progress_entry = self.progress_service.get_word_progress(word_id)
        if progress_entry:
            vocab_entry["progress"] = progress_entry
        else:
            vocab_entry["progress"] = {
                "attempts": 0,
                "successes": 0,
                "last_seen": None,
                "review_intervals": [],
                "last_attempt_was_failure": False,
                "easiness_factor": 2.5,
                "interval": 0,
            }

        return vocab_entry

    def update_word_progress(self, word_id: str, success: bool):
        """Update progress for a practiced word.

        Args:
            word_id: The word ID (e.g., 'word_000001')
            success: Whether the practice attempt was successful
        """
        self.progress_service.update_progress(word_id, success)

    def get_practice_stats(self) -> Dict:
        """Get overall practice statistics.

        Returns:
            Dictionary with practice statistics
        """
        all_words = self.vocabulary_service.get_all_words()
        total_words = len(all_words)

        if total_words == 0:
            return {
                "total_words": 0,
                "words_started": 0,
                "words_mastered": 0,
                "total_attempts": 0,
                "total_successes": 0,
                "success_rate": 0.0,
            }

        total_attempts = 0
        total_successes = 0
        words_started = 0
        words_mastered = 0

        for word in all_words:
            progress = self.progress_service.get_word_progress(word)
            if progress:
                words_started += 1
                total_attempts += progress["attempts"]
                total_successes += progress["successes"]

                # Check if word is mastered
                if is_mastered(progress):
                    words_mastered += 1

        return {
            "total_words": total_words,
            "words_started": words_started,
            "words_mastered": words_mastered,
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "success_rate": (total_successes / total_attempts) if total_attempts > 0 else 0.0,
        }

    def get_word_suggestions(
        self, current_word: str, num_suggestions: int = 3
    ) -> List[Tuple[str, float]]:
        """Get similar words as suggestions, with similarity scores.

        Args:
            current_word: Current word being practiced
            num_suggestions: Number of suggestions to return

        Returns:
            List of (word, similarity_score) tuples
        """
        all_words = self.vocabulary_service.get_all_words()
        if len(all_words) <= 1:
            return []

        current_entry = self.vocabulary_service.get_word(current_word)
        if not current_entry:
            return []

        # Calculate similarity scores based on translations and example sentences
        similarities = []
        for word in all_words:
            if word == current_word:
                continue

            entry = self.vocabulary_service.get_word(word)
            if not entry:
                continue

            score = 0.0

            # Compare translations
            for trans1 in current_entry["translations"]:
                for trans2 in entry["translations"]:
                    if any(
                        word in trans1.lower() and word in trans2.lower() for word in trans1.split()
                    ):
                        score += 0.5

            # Compare example sentences
            for sent1 in current_entry["example_sentences"]:
                for sent2 in entry["example_sentences"]:
                    # Compare Japanese sentences
                    if any(
                        word in sent1["jp"].lower() and word in sent2["jp"].lower()
                        for word in sent1["jp"].split()
                    ):
                        score += 0.3
                    # Compare French sentences
                    if any(
                        word in sent1["fr"].lower() and word in sent2["fr"].lower()
                        for word in sent1["fr"].split()
                    ):
                        score += 0.2

            if score > 0:
                similarities.append((word, score))

        # Sort by similarity score and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:num_suggestions]
