# Japanese Vocabulary Learning Tool

A command-line tool for learning Japanese vocabulary with spaced repetition and Firebase integration.

[![Tests](https://github.com/AurelienNioche/vocabulary-learning/actions/workflows/test.yml/badge.svg)](https://github.com/AurelienNioche/vocabulary-learning/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/AurelienNioche/vocabulary-learning/branch/main/graph/badge.svg)](https://codecov.io/gh/AurelienNioche/vocabulary-learning)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Features

### Core Features
- Interactive command-line interface with Vim-like commands
- Japanese text support (hiragana, katakana, kanji)
- Advanced spaced repetition system (based on SuperMemo 2)
- Progress tracking and statistics

### Cloud Integration
- Firebase integration for data backup
- Local JSON backup for offline use

### Learning Features
- Smart answer validation:
  - Handles multiple French translations
  - Detects and suggests corrections for French accents
  - Identifies minor typos and asks for confirmation
- Example sentences for context
- Detailed statistics for each word
- Progress tracking with success rates

### Spaced Repetition Algorithm
The tool uses an enhanced version of the SuperMemo 2 algorithm for optimal learning:

1. **Initial Learning**:
   - First success: 5-minute interval
   - Second success: 24-hour interval
   - Subsequent intervals: Calculated using easiness factor

2. **Interval Progression**:
   - Each successful review increases the interval by the easiness factor
   - Initial easiness factor: 2.5
   - Successful reviews: Increase factor by 0.1
   - Failed reviews: Decrease factor by 0.2 (minimum 1.3)

3. **Review Priority**:
   - Based on success rate, time since last review, and review intervals
   - Prioritizes words with:
     - Lower success rates
     - Overdue reviews
     - Recent failures
   - Limits active learning to 8 words at a time

### Vim-like Commands
- `:h` - Show help
- `:q` - Quit program (saves progress)
- `:m` - Return to menu
- `:s` - Show word statistics
- `:e` - Show example sentence
- `:d` - Don't know (show answer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AurelienNioche/vocabulary-learning.git
cd vocabulary-learning
```

2. Install dependencies:
```bash
pip install -e ".[dev]"  # Install with development dependencies
# or
pip install -e .         # Install only runtime dependencies
```

3. Set up Firebase:
   - Create a Firebase project
   - Download service account credentials
   - Create `.env` file with:
     ```
     FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
     FIREBASE_DATABASE_URL=your-database-url
     FIREBASE_USER_EMAIL=your-email
     ```

## Usage

1. Run the program:
```bash
vocab
```

2. Choose from the main menu:
- Practice vocabulary
- Show progress
- Add vocabulary
- Reset progress
- Quit

3. During practice:
- Type your French translation
- Use `:d` if you don't know the answer
- Use `:e` to see example sentences
- Use `:s` to see your statistics for the current word

## Adding Vocabulary

- Enter Japanese words in hiragana or kanji
- Add multiple French translations using slashes (e.g., "bonjour/salut")
- Optional example sentences for context
- Words are automatically assigned sequential IDs

## Progress Tracking

Your progress is:
- Saved automatically after each answer
- Synced with Firebase (if configured)
- Backed up locally in JSON format
- Tracked with detailed statistics including:
  - Success rate
  - Review intervals
  - Last practice time
  - Easiness factor

## Development

- Tests: `pytest tests/`
- Code formatting: `black .`
- Import sorting: `isort .`
- Linting: `flake8`
- Pre-commit hooks available

## Tips

- Use `:d` when you don't know a word instead of guessing
- Check example sentences with `:e` to learn context
- Review your statistics with `:s` to track progress
- Let the spaced repetition system guide your learning pace

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.