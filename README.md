# Japanese Vocabulary Learning Tool

A command-line tool for learning Japanese vocabulary with spaced repetition and Firebase integration.

## Features

### Core Features
- Interactive command-line interface with Vim-like commands
- Japanese text support (hiragana, katakana, kanji)
- Spaced repetition learning system
- Progress tracking and statistics
- Clean and modular code structure

### Cloud Integration
- Firebase integration for cloud sync
- Local JSON backup
- Automatic data synchronization
- Secure user authentication

### Learning Features
- Smart answer validation:
  - Handles multiple correct translations
  - Detects and suggests corrections for accents
  - Identifies minor typos and asks for confirmation
- Example sentences with translations
- Detailed statistics for each word
- Progress tracking with success rates

### Vim-like Commands
- `:h` - Show help
- `:q` - Quit to menu (saves progress)
- `:q!` - Force quit program
- `:w` - Show save status
- `:s` - Show word statistics
- `:S` - Show all statistics
- `:e` - Show example with translation
- `:d` - Don't know (show answer)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd vocabulary-learning
```

2. Install dependencies:
```bash
pip install -e .
```

## Usage

1. Run the program:
```bash
python vocab_learner.py
```

2. Choose from the main menu:
- Practice vocabulary
- Show progress
- Add vocabulary
- Quit

3. During practice:
- Type your answer or use Vim-like commands
- Use `:d` if you don't know the answer
- Use `:e` to see example sentences with translations
- Use `:s` to see your statistics for the current word

## Adding Vocabulary

- Enter Japanese words in any form (hiragana, kanji, romaji)
- Add multiple translations using slashes (e.g., "bonjour/salut")
- Optional kanji and example sentences
- Automatic suggestions for kanji and translations
- Words are automatically assigned sequential IDs (e.g., word_000001)

## Progress Tracking

Your progress is:
- Saved automatically after each answer
- Synced with Firebase in real-time
- Backed up locally in JSON format
- Tracked with detailed statistics

## Tips

- Use `:d` when you don't know a word instead of guessing
- Check example sentences with `:e` to learn context
- Review your progress regularly with `:S`
- Your progress is automatically backed up to Firebase