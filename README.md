# Japanese Vocabulary Learning Tool

An interactive command-line tool for learning Japanese vocabulary with spaced repetition and git-based progress tracking.

## Features

### Core Features
- Learn Japanese vocabulary with French translations
- Support for hiragana, katakana, kanji, and romaji input
- Automatic conversion between different Japanese writing systems
- Smart spaced repetition system based on your performance
- Progress tracking and statistics

### Practice Mode
- Intelligent word selection based on your learning history
- Multiple correct answers support (separated by slashes)
- Typo tolerance with user confirmation
- Accent-insensitive answer checking
- Example sentences with translations

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

### Firebase Setup

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Set up Authentication:
   - In the left sidebar, click "Authentication"
   - Click "Get Started"
   - Enable Email/Password authentication method
   - Add your first user in the "Users" tab with your email and password

4. Set up Environment Variables:
   - Create a `.env` file in the project root if it doesn't exist
   - Add the following lines:
```
FIREBASE_CREDENTIALS_PATH="${HOME}/.config/vocabulary-learning/vocabulary-learning-9bd6e-firebase-adminsdk-fbsvc-b89ec4a8a2.json"
FIREBASE_USER_EMAIL="your-email@example.com"
FIREBASE_USER_PASSWORD="your-password"
FIREBASE_DATABASE_URL="https://vocabulary-learning-9bd6e-default-rtdb.europe-west1.firebasedatabase.app"
```
   - Replace `your-email@example.com` and `your-password` with your Firebase authentication credentials
   - The `FIREBASE_CREDENTIALS_PATH` should point to your Firebase Admin SDK credentials file
   - Make sure the `FIREBASE_DATABASE_URL` matches your database region (europe-west1 in this case)

5. Set up Realtime Database:
   - In the left sidebar, click "Realtime Database"
   - Click "Create Database"
   - Choose "Production mode"
   - Select your preferred region (e.g., europe-west1)
   - Click "Enable"

6. Configure Security Rules:
   - In Realtime Database, click the "Rules" tab
   - Set the following security rules:
```json
{
  "rules": {
    "progress": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid",
        "$word": {
          ".validate": "newData.hasChildren(['attempts', 'successes', 'last_seen', 'review_intervals', 'last_attempt_was_failure'])"
        }
      }
    }
  }
}
```

7. Initialize Database Structure:
   - In the Realtime Database interface, click the three dots (⋮) menu button
   - Select "Import JSON"
   - Upload the provided `example_firebase_data.json` file or copy its contents
   - Replace `user_id` in the JSON with your actual Firebase user ID
   - Click "Import"

The database structure should look like:
```
progress/
  └─ <your-firebase-user-id>/
     └─ ねんまつねんし/
        ├─ attempts: 0
        ├─ successes: 0
        ├─ last_seen: "2025-02-07T21:57:51.254923"
        ├─ last_attempt_was_failure: false
        └─ review_intervals: []
```

These security rules ensure that:
- Each user can only read and write their own progress data
- Data structure is validated to maintain consistency
- No unauthorized access is possible

This structure will be automatically updated as you use the vocabulary learning program.

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