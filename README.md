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
- Word mastery tracking

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
     - Last attempt result (failed words get 20% higher priority)
   - Words not due for review are skipped
   - New words get high but not maximum priority
   - Priority is scaled based on active word count

4. **Word Mastery Criteria**:
   - A word is considered mastered when:
     - It has at least 5 successful reviews
     - It maintains a success rate of 90% or higher
   - Mastered words are excluded from regular review
   - System focuses on words still being learned

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

## Quick Installation (Docker)

The easiest way to install is using our automated setup script:

1. Clone the repository:
```bash
git clone https://github.com/AurelienNioche/vocabulary-learning.git
cd vocabulary-learning
```

2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

The script will:
- Check if Docker is installed
- Create necessary directories
- Guide you through Firebase configuration
- Build the Docker image
- Create the `vocab` command in your PATH

3. Start the application:
```bash
vocab
```

That's it! The `vocab` command will be available system-wide, and your data will be automatically persisted in the appropriate directories.

### OS-Specific Notes

#### macOS
- The script will install the `vocab` command in `~/bin`
- If `~/bin` doesn't exist, it will be created and added to your PATH
- You may need to run `source ~/.zshrc` after first installation
- Data is stored in `~/Library/Application Support/VocabularyLearning/`

#### Linux
- The script will install the `vocab` command in `/usr/local/bin`
- May require sudo access for installation
- Fallback to `./vocab-docker` if system-wide installation fails
- Data is stored in `~/.local/share/vocabulary-learning/`

### Data Storage

Your data will be organized in the following structure:
- `data/` - Vocabulary and progress files
- `firebase/` - Firebase credentials
- `.env` - Environment configuration

The location depends on your operating system:
- macOS: `~/Library/Application Support/VocabularyLearning/`
- Linux: `~/.local/share/vocabulary-learning/`

This follows OS conventions for application data and ensures your data persists independently of the installation directory.

## Manual Docker Installation

If you prefer to set everything up manually, follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/AurelienNioche/vocabulary-learning.git
cd vocabulary-learning
```

2. Create necessary directories:
```bash
mkdir -p vocabulary_learning/data
```

3. Set up Firebase credentials:
```bash
mkdir -p .firebase
# Copy your Firebase credentials to .firebase/credentials.json
```

4. Create a `.env` file:
```bash
FIREBASE_CREDENTIALS_PATH=/app/.firebase/credentials.json
FIREBASE_DATABASE_URL=your-database-url
FIREBASE_USER_EMAIL=your-email
```

5. Build and run with Docker:
```bash
# Build the image
docker build -t vocab-learning .

# Run the container
docker run -it --rm \
  -v $(pwd)/vocabulary_learning/data:/app/vocabulary_learning/data \
  -v $(pwd)/.firebase:/app/.firebase \
  -v $(pwd)/.env:/app/.env \
  vocab-learning
```

The Docker container:
- Persists your vocabulary and progress in `vocabulary_learning/data/`
- Uses your Firebase credentials from `.firebase/`
- Loads environment variables from `.env`
- Runs in interactive mode for CLI usage

## Updating the Application

If you're using Docker, follow these steps to update to the latest version:

1. Pull the latest changes:
```bash
git pull origin main
```

2. Rebuild the Docker image:
```bash
docker build -t vocab-learning .
```

3. Run the container as usual:
```bash
docker run -it --rm \
  -v $(pwd)/vocabulary_learning/data:/app/vocabulary_learning/data \
  -v $(pwd)/.firebase:/app/.firebase \
  -v $(pwd)/.env:/app/.env \
  vocab-learning
```

Your data and progress will be preserved as they are stored in the mounted volumes.

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
  - Mastery status

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
- Focus on mastering a small set of words before adding more

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.