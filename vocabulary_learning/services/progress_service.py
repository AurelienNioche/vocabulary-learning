"""Service layer for progress tracking and spaced repetition."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from firebase_admin import db
from rich.console import Console

from vocabulary_learning.core.progress_tracking import (
    calculate_priority,
    count_active_learning_words,
)


class ProgressService:
    def __init__(
        self,
        progress_file: str,
        progress_ref: Optional[db.Reference] = None,
        console: Optional[Console] = None,
    ):
        """Initialize progress service.

        Args:
            progress_file: Path to progress JSON file
            progress_ref: Firebase reference for progress
            console: Rich console for output (optional)
        """
        self.progress_file = progress_file
        self.progress_ref = progress_ref
        self.console = console or Console()

        # Ensure data directory exists
        data_dir = Path(progress_file).parent
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load initial progress
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load progress from Firebase or local JSON file."""
        if self.progress_ref is not None:
            try:
                # Try to load from Firebase
                progress = self.progress_ref.get() or {}
                return progress
            except Exception as e:
                self.console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Falling back to local file...[/yellow]")

        # Fallback to local file
        if Path(self.progress_file).exists():
            with open(self.progress_file, "r") as f:
                progress = json.load(f)
                # Migrate old progress data to new format
                for word in progress:
                    if "review_intervals" not in progress[word]:
                        progress[word]["review_intervals"] = []
                    if "last_attempt_was_failure" not in progress[word]:
                        progress[word]["last_attempt_was_failure"] = False
                return progress
        return {}

    def save_progress(self):
        """Save progress to Firebase and local backup."""
        # Ensure directory exists
        Path(self.progress_file).parent.mkdir(parents=True, exist_ok=True)

        # Always save to local file as backup
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

        # Try to save to Firebase
        if self.progress_ref is not None:
            try:
                self.progress_ref.set(self.progress)
            except Exception as e:
                self.console.print(f"[yellow]Failed to save to Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Progress saved to local file only.[/yellow]")

    def update_progress(self, word_id: str, success: bool):
        """Update progress for a given word.

        Args:
            word_id: The word ID (e.g., 'word_000001')
            success: Whether the attempt was successful
        """
        if word_id not in self.progress:
            self.progress[word_id] = {
                "attempts": 0,
                "successes": 0,
                "last_seen": datetime.now().isoformat(),
                "review_intervals": [],
                "last_attempt_was_failure": False,
                "easiness_factor": 2.5,
                "interval": 0,
            }
        elif "interval" not in self.progress[word_id]:
            # Add interval if missing in existing progress data
            self.progress[word_id]["interval"] = 0
            self.progress[word_id]["easiness_factor"] = self.progress[word_id].get(
                "easiness_factor", 2.5
            )
            self.progress[word_id]["last_attempt_was_failure"] = self.progress[word_id].get(
                "last_attempt_was_failure", False
            )

        # Calculate and store interval since last review
        last_seen = datetime.fromisoformat(self.progress[word_id]["last_seen"])
        hours_since_last = (datetime.now() - last_seen).total_seconds() / 3600.0
        self.progress[word_id]["review_intervals"].append(hours_since_last)

        # Keep only last 10 intervals
        if len(self.progress[word_id]["review_intervals"]) > 10:
            self.progress[word_id]["review_intervals"] = self.progress[word_id]["review_intervals"][
                -10:
            ]

        self.progress[word_id]["attempts"] += 1
        if success:
            self.progress[word_id]["successes"] += 1
            # Update SuperMemo 2 parameters
            if self.progress[word_id]["interval"] == 0:
                self.progress[word_id]["interval"] = 0.0333  # First success: wait 2 minutes
            elif self.progress[word_id]["interval"] == 0.0333:
                self.progress[word_id]["interval"] = 24  # Second success: wait 1 day
            else:
                # Calculate new interval using easiness factor
                self.progress[word_id]["interval"] *= self.progress[word_id]["easiness_factor"]

            # Update easiness factor (increase for correct answers)
            self.progress[word_id]["easiness_factor"] = max(
                1.3, self.progress[word_id]["easiness_factor"] + 0.1
            )
            self.progress[word_id]["last_attempt_was_failure"] = False
        else:
            # Decrease interval and easiness factor for incorrect answers
            self.progress[word_id]["interval"] = max(
                0.0333, self.progress[word_id]["interval"] * 0.5
            )
            self.progress[word_id]["easiness_factor"] = max(
                1.3, self.progress[word_id]["easiness_factor"] - 0.2
            )
            self.progress[word_id]["last_attempt_was_failure"] = True

        self.progress[word_id]["last_seen"] = datetime.now().isoformat()
        self.save_progress()

    def get_word_priority(self, word_id: str, active_words_count: Optional[int] = None) -> float:
        """Calculate priority score for a word.

        Args:
            word_id: The word ID (e.g., 'word_000001')
            active_words_count: Number of active learning words (optional)

        Returns:
            Priority score between 0.0 and 1.0
        """
        if active_words_count is None:
            active_words_count = self.count_active_words()

        word_data = self.progress.get(word_id)
        return calculate_priority(word_data, active_words_count)

    def get_word_progress(self, word_id: str) -> Optional[Dict]:
        """Get progress data for a specific word.

        Args:
            word_id: The word ID (e.g., 'word_000001')

        Returns:
            Progress data dictionary or None if not found
        """
        return self.progress.get(word_id)

    def count_active_words(self) -> int:
        """Count how many words are being actively learned."""
        return count_active_learning_words(self.progress)

    def reset_progress(self, create_backup: bool = True) -> bool:
        """Reset all learning progress."""
        try:
            # Backup current progress
            if create_backup and Path(self.progress_file).exists():
                backup_file = (
                    f"{self.progress_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                with (
                    open(self.progress_file, "r", encoding="utf-8") as src,
                    open(backup_file, "w", encoding="utf-8") as dst,
                ):
                    dst.write(src.read())
                self.console.print(f"[dim]Progress backed up to: {backup_file}[/dim]")

            # Reset progress
            self.progress.clear()
            self.save_progress()

            return True
        except Exception as e:
            self.console.print(f"[red]Error resetting progress: {str(e)}[/red]")
            return False
