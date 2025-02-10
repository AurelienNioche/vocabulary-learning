from datetime import datetime
import json
from typing import Dict, Any
import math

class ProgressManager:
    def __init__(self, progress_file: str, firebase_ref=None):
        self.progress_file = progress_file
        self.firebase_ref = firebase_ref
        self.progress = {}
        self.load_progress()

    def load_progress(self) -> None:
        if self.firebase_ref:
            try:
                self.progress = self.firebase_ref.get() or {}
                return
            except Exception:
                pass

        try:
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        except FileNotFoundError:
            self.progress = {}

    def save_progress(self) -> None:
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

        if self.firebase_ref:
            try:
                self.firebase_ref.set(self.progress)
            except Exception:
                pass

    def calculate_priority(self, word: str, word_data: Dict[str, Any]) -> float:
        """Calculate priority score for a word."""
        if word_data is None:
            return 1.0 if self.count_active_words() < 8 else 0.0

        successes = word_data.get('successes', 0)
        attempts = word_data.get('attempts', 0)
        success_rate = (successes / max(attempts, 1)) * 100

        if attempts >= 10:
            if success_rate >= 80:
                return 0.1 + random.random() * 0.1
            elif success_rate >= 60:
                return 0.3 + random.random() * 0.1
            else:
                return 0.7 + random.random() * 0.1
        else:
            return 0.8 + random.random() * 0.1

    def count_active_words(self) -> int:
        """Count words being actively learned."""
        return sum(1 for data in self.progress.values()
                  if data.get('attempts', 0) >= 10 and
                  (data.get('successes', 0) / data.get('attempts', 1)) * 100 < 80)
