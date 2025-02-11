# Japanese Vocabulary Learning Tool

A command-line tool for learning Japanese vocabulary with spaced repetition and Firebase integration.

## Features

- Interactive command-line interface with Vim-like commands
- Japanese text support (hiragana, katakana, kanji)
- Spaced repetition learning system
- Progress tracking and statistics
- Firebase integration for cloud sync
- Local JSON backup
- Smart answer checking with typo tolerance
- Example sentences with translations
<<<<<<< HEAD
- Clean and modular code structure
=======

### Vim-like Commands
- `:h` - Show help
- `:q` - Quit to menu (saves progress)
- `:q!` - Force quit program
- `:w` - Show save status
- `:s` - Show word statistics
- `:S` - Show all statistics
- `:e` - Show example with translation
- `:d` - Don't know (show answer)

### Git Integration
- Automatic commits of your progress
- Automatic push to remote repository
- Timestamped commits for tracking learning sessions
- Progress backup on every quit or interrupt

### Learning Features
- Smart answer validation:
  - Handles multiple correct translations
  - Detects and suggests corrections for accents
  - Identifies minor typos and asks for confirmation
- Example sentences with translations
- Detailed statistics for each word
- Progress tracking with success rates
>>>>>>> parent of 734c9ca (using firebase)

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

## Progress Tracking

Your progress is:
- Saved automatically after each answer
- Committed to git when you quit
- Pushed to your remote repository
- Tracked with detailed statistics

## Tips

- Use `:d` when you don't know a word instead of guessing
- Check example sentences with `:e` to learn context
- Review your progress regularly with `:S`
- Your progress is automatically backed up via git