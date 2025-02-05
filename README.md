# Japanese-French Vocabulary Learner

A command-line application for learning Japanese-French vocabulary using spaced repetition principles.

## Features

- Learns from a CSV file containing Japanese-French word pairs
- Uses spaced repetition to optimize learning
- Tracks progress and adapts to your learning pace
- Prioritizes words you find difficult
- Ensures regular exposure to new words

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Add your vocabulary words to `vocabulary.csv` in the format:
```csv
japanese,french
こんにちは,bonjour
```

2. Run the application:
```bash
python vocab_learner.py
```

3. Follow the prompts to practice your vocabulary:
- Type your answer in French when shown a Japanese word
- Press Enter to submit your answer
- Type 'q' to quit at any time

## Progress Tracking

The application automatically tracks your progress in `progress.json`. This includes:
- Number of attempts for each word
- Success rate
- Last time each word was practiced

The spaced repetition system will:
- Show difficult words more frequently
- Space out words you know well
- Regularly introduce new words 