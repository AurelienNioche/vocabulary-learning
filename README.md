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
- Smart word selection algorithm
- Temporal decay-based word mastery tracking

### Cloud Integration
- Firebase integration for data backup
- Local JSON backup for offline use
- Automatic sync between devices

### Learning Features
- Smart answer validation:
  - Handles multiple French translations
  - Detects and suggests corrections for French accents
  - Identifies minor typos and asks for confirmation
- Example sentences for context
- Detailed statistics for each word
- Progress tracking with success rates
- Word mastery criteria

### Spaced Repetition Algorithm
The tool uses an enhanced version of the SuperMemo 2 algorithm for optimal learning:

1. **Initial Learning**:
   - First success: 2-minute interval
   - Second success: 24-hour interval
   - Subsequent intervals: Calculated using easiness factor

2. **Interval Progression**:
   - Each successful review increases the interval by the easiness factor
   - Initial easiness factor: 2.5
   - Successful reviews: Increase factor by 0.1
   - Failed reviews: Decrease factor by 0.2 (minimum 1.3)

3. **Word Selection Priority**:
   - Based on multiple factors:
     - Time since last review relative to scheduled interval
     - Success rate (lower rates get higher priority)
     - Number of attempts (newer words get higher priority)
     - Last attempt result (failed words get higher priority)
   - Words not due for review are skipped
   - New words get high but not maximum priority
   - Priority is scaled based on active word count

4. **Word Mastery Criteria**:
   - A word is considered mastered when:
     - It has at least 5 successful reviews total
     - It maintains a weighted success rate of 90% or higher
   - Success rate calculation uses temporal decay:
     - Recent attempts have more weight than older ones
     - 30-day half-life (attempts from 30 days ago have half the weight)
     - Exponential decay function: weight = e^(-λt)
   - This means:
     - Recent performance matters more than historical performance
     - A word can lose mastery status if recent performance drops
     - Old failures gradually "fade away" in importance
     - Very recent failures have strong impact on mastery status
   - Mastered words are excluded from regular review
   - System focuses on words still being learned

### Vim-like Commands
- `:h` - Show help
- `:q` - Quit program (saves progress)
- `:m` - Return to menu
- `:s` - Show word statistics
- `:S` - Show all statistics
- `:e` - Show example sentence
- `:d` - Don't know (show answer)

## Requirements

- Python 3.10 or higher
- Docker (for containerized installation)
- Firebase account (for cloud sync)

## Installation

### Quick Installation (Recommended)

The easiest way to install is using our automated setup script:

```bash
git clone https://github.com/AurelienNioche/vocabulary-learning.git
cd vocabulary-learning
chmod +x install.sh
./install.sh
```

The script will:
- Check for required dependencies
- Create necessary directories
- Guide you through Firebase configuration
- Set up your timezone
- Build the Docker image
- Create the `vocab` command in your PATH

### Manual Installation

If you prefer to set everything up manually:

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
     TIMEZONE=your-timezone  # e.g., Europe/Helsinki
     ```

### Docker Installation

For a clean, isolated environment:

1. Build the image:
```bash
docker build -t vocab-learning .
```

2. Run the container:
```bash
docker run -it --rm \
  -v "$(pwd)/data":/app/vocabulary_learning/data \
  -v "$(pwd)/firebase":/app/firebase \
  -v "$(pwd)/.env:/app/.env \
  vocab-learning
```

## Data Storage

Your data is organized in the following structure:
- `data/` - Vocabulary and progress files
- `firebase/` - Firebase credentials
- `.env` - Environment configuration

Location by OS:
- macOS: `~/Library/Application Support/VocabularyLearning/`
- Linux: `~/.local/share/vocabulary-learning/`

## Usage

1. Start the application:
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
- Use Vim-like commands for navigation
- View statistics and examples
- Track your progress

## Adding Vocabulary

1. Choose "Add vocabulary" from the main menu
2. Enter:
   - Japanese word (hiragana or kanji)
   - Multiple French translations (separated by slashes)
   - Example sentence (optional)
   - Notes (optional)

## Updating

1. Pull latest changes:
```bash
git pull origin main
```

2. Rebuild (if using Docker):
```bash
docker build -t vocab-learning .
```

Your data and progress will be preserved as they are stored separately.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests:
```bash
pytest
```
5. Submit a pull request

## License

This project is licensed under the AGPL v3 License - see the LICENSE file for details.