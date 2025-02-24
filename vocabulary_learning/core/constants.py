"""Constants used throughout the vocabulary learning application."""

from pathlib import Path

# Progress Tracking Constants
INITIAL_EASINESS_FACTOR = 2.5
MIN_EASINESS_FACTOR = 1.3
EASINESS_INCREASE = 0.1
EASINESS_DECREASE = 0.2
FIRST_SUCCESS_INTERVAL = 0.0333  # 2 minutes in hours
SECOND_SUCCESS_INTERVAL = 24.0  # 1 day in hours
MAX_ACTIVE_WORDS = 8
MASTERY_MIN_SUCCESSES = 5
MASTERY_SUCCESS_RATE = 0.85
FAILED_WORD_PRIORITY_BONUS = 0.3

# Time and Date Constants
DEFAULT_TIMEZONE = "Europe/Helsinki"
HALF_LIFE_DAYS = 30.0  # Number of days after which weight is halved
DECAY_RATE = 0.693 / (HALF_LIFE_DAYS * 24)  # ln(2) / (half_life in hours)

# File System Constants
DATA_DIR_NAME = "VocabularyLearning"
MACOS_DATA_DIR = Path.home() / "Library/Application Support" / DATA_DIR_NAME
LINUX_DATA_DIR = Path.home() / ".local/share/vocabulary-learning"

# Firebase Constants
FIREBASE_PATHS = {
    "progress": "progress",
    "vocabulary": "vocabulary",
}

# UI Constants
MAX_REVIEW_INTERVALS_HISTORY = 10
DEFAULT_PRACTICE_WORDS = 10
SUCCESS_MARK = "[green]✓[/green]"
FAILURE_MARK = "[red]✗[/red]"

# Vim-like Commands
VIM_COMMANDS = {
    ":q": "quit program",
    ":m": "return to menu",
    ":h": "show help",
    ":s": "show word statistics",
    ":S": "show all statistics",
    ":e": "show example sentence",
    ":d": "don't know (show answer)",
}

# Data Validation Constants
REQUIRED_VOCABULARY_COLUMNS = ["japanese", "kanji", "french", "example_sentence"]
REQUIRED_PROGRESS_FIELDS = [
    "attempts",
    "successes",
    "interval",
    "last_attempt_was_failure",
    "last_seen",
    "review_intervals",
    "easiness_factor",
]

# Text Processing Constants
TYPO_SIMILARITY_THRESHOLD = 0.85  # Threshold for considering a typo vs a different word

# Word ID Format Constants
WORD_ID_DIGITS = 6  # Number of digits in word ID (e.g., "000001")
WORD_ID_PREFIX = "word_"  # Prefix for word IDs

# File Names
VOCABULARY_FILE = "vocabulary.json"
PROGRESS_FILE = "progress.json"
CREDENTIALS_FILE = "credentials.json"
ENV_FILE = ".env"
