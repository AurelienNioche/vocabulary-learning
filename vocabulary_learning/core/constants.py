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

# File Names
VOCABULARY_FILE = "vocabulary.json"
PROGRESS_FILE = "progress.json"
CREDENTIALS_FILE = "credentials.json"
ENV_FILE = ".env"
