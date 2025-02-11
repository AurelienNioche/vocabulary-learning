import pandas as pd
import random
from datetime import datetime, timedelta
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
import os
import signal
import math
from googletrans import Translator
import pykakasi
import time
import unicodedata
import re
from difflib import SequenceMatcher
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db, auth
import sys

# Get the package root directory
PACKAGE_ROOT = Path(__file__).parent

class VocabularyLearner:
    def __init__(self, vocab_file="data/vocabulary.json", progress_file="data/progress.json"):
        self.vocab_file = str(PACKAGE_ROOT / vocab_file)
        self.progress_file = str(PACKAGE_ROOT / progress_file)
        
        # Ensure data directory exists
        data_dir = Path(self.vocab_file).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        self.console = Console()
        
        # Initialize Firebase
        load_dotenv()
        cred_path = os.path.expandvars(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        
        if not os.path.exists(cred_path):
            self.console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
            exit(1)
            
        try:
            try:
                app = firebase_admin.get_app()
                self.console.print("[dim]Using existing Firebase connection[/dim]")
            except ValueError:
                cred = credentials.Certificate(cred_path)
                app = firebase_admin.initialize_app(cred, {
                    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
                })
            
            # Get user credentials
            email = os.getenv('FIREBASE_USER_EMAIL')
            if not email:
                raise ValueError("Firebase user email not found in .env")
            
            # Get user ID
            user = auth.get_user_by_email(email)
            user_id = user.uid
            self.console.print(f"[dim]Authenticated as: {email}[/dim]")
            
            # Set up database references
            self.progress_ref = db.reference(f'/progress/{user_id}')
            self.vocab_ref = db.reference(f'/vocabulary/{user_id}')
            self.console.print("[green]Successfully connected to Firebase![/green]")
            
        except Exception as e:
            self.console.print(f"[red]Failed to initialize Firebase: {str(e)}[/red]")
            self.progress_ref = None
            self.vocab_ref = None
            self.console.print("[yellow]Falling back to local storage...[/yellow]")
        
        self.load_vocabulary()
        self.load_progress()
        
        # Setup signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Vim-like commands
        self.vim_commands = {
            ':q': 'quit program',
            ':m': 'return to menu',
            ':h': 'show help',
            ':s': 'show word statistics',
            ':S': 'show all statistics',
            ':e': 'show example',
            ':d': 'show answer (don\'t know)'
        }
        
        self.last_save_time = datetime.now()
        # Initialize Japanese text converter
        self.kks = pykakasi.kakasi()
        # Initialize translator
        self.translator = Translator()
        
        # Common romaji to hiragana mappings
        self.romaji_to_hiragana = {
            'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え', 'o': 'お',
            'ka': 'か', 'ki': 'き', 'ku': 'く', 'ke': 'け', 'ko': 'こ',
            'sa': 'さ', 'shi': 'し', 'su': 'す', 'se': 'せ', 'so': 'そ',
            'ta': 'た', 'chi': 'ち', 'tsu': 'つ', 'te': 'て', 'to': 'と',
            'na': 'な', 'ni': 'に', 'nu': 'ぬ', 'ne': 'ね', 'no': 'の',
            'ha': 'は', 'hi': 'ひ', 'fu': 'ふ', 'he': 'へ', 'ho': 'ほ',
            'ma': 'ま', 'mi': 'み', 'mu': 'む', 'me': 'め', 'mo': 'も',
            'ya': 'や', 'yu': 'ゆ', 'yo': 'よ',
            'ra': 'ら', 'ri': 'り', 'ru': 'る', 're': 'れ', 'ro': 'ろ',
            'wa': 'わ', 'wo': 'を', 'n': 'ん',
            'ga': 'が', 'gi': 'ぎ', 'gu': 'ぐ', 'ge': 'げ', 'go': 'ご',
            'za': 'ざ', 'ji': 'じ', 'zu': 'ず', 'ze': 'ぜ', 'zo': 'ぞ',
            'da': 'だ', 'di': 'ぢ', 'du': 'づ', 'de': 'で', 'do': 'ど',
            'ba': 'ば', 'bi': 'び', 'bu': 'ぶ', 'be': 'べ', 'bo': 'ぼ',
            'pa': 'ぱ', 'pi': 'ぴ', 'pu': 'ぷ', 'pe': 'ぺ', 'po': 'ぽ',
            'kya': 'きゃ', 'kyu': 'きゅ', 'kyo': 'きょ',
            'sha': 'しゃ', 'shu': 'しゅ', 'sho': 'しょ',
            'cha': 'ちゃ', 'chu': 'ちゅ', 'cho': 'ちょ',
            'nya': 'にゃ', 'nyu': 'にゅ', 'nyo': 'にょ',
            'hya': 'ひゃ', 'hyu': 'ひゅ', 'hyo': 'ひょ',
            'mya': 'みゃ', 'myu': 'みゅ', 'myo': 'みょ',
            'rya': 'りゃ', 'ryu': 'りゅ', 'ryo': 'りょ',
            'gya': 'ぎゃ', 'gyu': 'ぎゅ', 'gyo': 'ぎょ',
            'ja': 'じゃ', 'ju': 'じゅ', 'jo': 'じょ',
            'bya': 'びゃ', 'byu': 'びゅ', 'byo': 'びょ',
            'pya': 'ぴゃ', 'pyu': 'ぴゅ', 'pyo': 'ぴょ',
            # Special cases for おう
            'ou': 'おう',
            'oo': 'おう',
            'oh': 'おう',
            'wo': 'を',
        }

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.console.print("\n\n[yellow]Saving progress...[/yellow]")
        self.save_progress()
        exit(0)

    def load_vocabulary(self):
        """Load vocabulary from JSON file."""
        try:
            with open(self.vocab_file, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
            
            if not vocab_data:
                self.vocabulary = pd.DataFrame(columns=['japanese', 'kanji', 'french', 'example_sentence'])
                self.console.print("[yellow]No vocabulary data found[/yellow]")
                return
            
            # Convert JSON data to DataFrame
            vocab_list = []
            for word_id, word_data in vocab_data.items():
                vocab_list.append({
                    'japanese': word_data['hiragana'],
                    'kanji': word_data['kanji'],
                    'french': word_data['french'],
                    'example_sentence': word_data['example_sentence']
                })
            
            self.vocabulary = pd.DataFrame(vocab_list)
            # Clean whitespace from entries
            self.vocabulary = self.vocabulary.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            # Remove any empty rows
            self.vocabulary = self.vocabulary.dropna(subset=['japanese', 'french'])
            self.console.print(f"[green]✓ Loaded {len(self.vocabulary)} words[/green]")
            
            # Show last progress update time if progress file exists
            if os.path.exists(self.progress_file):
                last_modified = datetime.fromtimestamp(os.path.getmtime(self.progress_file))
                time_diff = datetime.now() - last_modified
                if time_diff.days > 0:
                    time_str = f"{time_diff.days} days ago"
                elif time_diff.seconds >= 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours} hours ago"
                else:
                    minutes = time_diff.seconds // 60
                    time_str = f"{minutes} minutes ago"
                self.console.print(f"[dim]Last progress update: {time_str}[/dim]")
            
        except FileNotFoundError:
            self.console.print("[yellow]No vocabulary file found[/yellow]")
            self.vocabulary = pd.DataFrame(columns=['japanese', 'kanji', 'french', 'example_sentence'])
        except json.JSONDecodeError:
            self.console.print("[red]Error: Invalid JSON format in vocabulary file[/red]")
            self.vocabulary = pd.DataFrame(columns=['japanese', 'kanji', 'french', 'example_sentence'])
        except Exception as e:
            self.console.print(f"[red]Error loading vocabulary: {str(e)}[/red]")
            self.vocabulary = pd.DataFrame(columns=['japanese', 'kanji', 'french', 'example_sentence'])

    def load_progress(self):
        """Load learning progress from Firebase or local JSON file."""
        if self.progress_ref is not None:
            try:
                # Try to load from Firebase
                self.progress = self.progress_ref.get() or {}
                return
            except Exception as e:
                self.console.print(f"[yellow]Failed to load from Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Falling back to local file...[/yellow]")
        
        # Fallback to local file
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
                # Migrate old progress data to new format
                for word in self.progress:
                    if 'review_intervals' not in self.progress[word]:
                        self.progress[word]['review_intervals'] = []
                    if 'last_attempt_was_failure' not in self.progress[word]:
                        self.progress[word]['last_attempt_was_failure'] = False
        else:
            self.progress = {}

    def save_progress(self):
        """Save learning progress to Firebase and local backup."""
        # Always save to local file as backup
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
        
        # Try to save to Firebase
        if self.progress_ref is not None:
            try:
                self.progress_ref.set(self.progress)
            except Exception as e:
                self.console.print(f"[yellow]Failed to save to Firebase: {str(e)}[/yellow]")
                self.console.print("[yellow]Progress saved to local file only.[/yellow]")

    def show_progress(self):
        """Display progress statistics in a nice table format."""
        table = Table(title="Vocabulary Progress")
        table.add_column("Japanese", style="bold")
        table.add_column("Kanji", style="bold cyan")
        table.add_column("French", style="bold green")
        table.add_column("Status", style="bold", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Attempts", justify="right")
        table.add_column("Last Practice", justify="right")

        for _, row in self.vocabulary.iterrows():
            japanese = row['japanese']
            kanji = row['kanji'] if pd.notna(row['kanji']) else ""
            french = row['french']
            stats = self.progress.get(japanese, {
                'attempts': 0,
                'successes': 0,
                'last_seen': 'Never'
            })
            
            attempts = stats['attempts']
            success_rate = (stats['successes'] / attempts * 100) if attempts > 0 else 0
            
            # Determine status
            if attempts >= 10:
                if success_rate >= 80:
                    status = "[green]Mastered[/green]"
                elif success_rate >= 60:
                    status = "[yellow]Learning[/yellow]"
                else:
                    status = "[red]Needs Work[/red]"
            else:
                status = f"[blue]{attempts}/10[/blue]"
            
            last_seen = stats['last_seen']
            if last_seen != 'Never':
                last_seen_date = datetime.fromisoformat(last_seen)
                days_ago = (datetime.now() - last_seen_date).days
                if days_ago == 0:
                    last_seen = "Today"
                elif days_ago == 1:
                    last_seen = "Yesterday"
                else:
                    last_seen = f"{days_ago} days ago"

            table.add_row(
                japanese,
                kanji,
                french,
                status,
                f"{success_rate:.1f}%",
                str(attempts),
                last_seen
            )

        self.console.print(table)

    def count_active_learning_words(self):
        """Count how many words are currently being actively learned (success rate < 80%)."""
        active_count = 0
        for word, data in self.progress.items():
            attempts = data.get('attempts', 0)
            successes = data.get('successes', 0)
            if attempts >= 10:  # Changed from 3 to 10 attempts minimum
                success_rate = (successes / attempts) * 100
                if success_rate < 80:  # Changed from 90% to 80%
                    active_count += 1
        return active_count

    def calculate_priority(self, word_data):
        """Calculate priority score for a word based on memory strength and spaced repetition principles."""
        MAX_ACTIVE_WORDS = 8  # Maximum number of words to learn at once
        MIN_ATTEMPTS = 10  # Minimum attempts before considering mastery
        
        # If this is a new word, check if we're already at max active words
        if word_data is None:
            if self.count_active_learning_words() >= MAX_ACTIVE_WORDS:
                return 0.0  # Don't introduce new words yet
            return 1.0  # Highest priority for new words if under the limit
        
        # Get basic stats
        successes = word_data.get('successes', 0)
        attempts = word_data.get('attempts', 0)
        # Avoid division by zero for new words
        success_rate = (successes / max(attempts, 1)) * 100
        
        # Different priority levels based on mastery
        if attempts >= MIN_ATTEMPTS:  # Only apply mastery levels after enough attempts
            if success_rate >= 80:  # Mastered
                return 0.1 + random.uniform(0, 0.1)  # Very low priority
            elif success_rate >= 60:  # Learning well
                return 0.3 + random.uniform(0, 0.1)  # Medium priority
            else:  # Needs work
                return 0.7 + random.uniform(0, 0.1)  # High priority
        else:  # Not enough attempts yet
            return 0.8 + random.uniform(0, 0.1)  # High priority for new words
        
        # Calculate time since last review
        last_seen = datetime.fromisoformat(word_data.get('last_seen', datetime.now().isoformat()))
        hours_since_last = (datetime.now() - last_seen).total_seconds() / 3600.0
        
        # Calculate optimal interval based on number of successful reviews
        # Using a modified version of SuperMemo 2 algorithm
        if successes == 0:
            optimal_interval = 4  # 4 hours for new words
        else:
            # Interval increases with each success, but resets partially on failure
            optimal_interval = 4 * (2 ** (successes - (attempts - successes)))
        
        # Calculate memory strength decay
        # Using Ebbinghaus forgetting curve: strength = e^(-time/decay_factor)
        decay_factor = optimal_interval * (1 + success_rate/100)  # Decay factor increases with success
        memory_strength = math.exp(-hours_since_last / decay_factor)
        
        # Priority is higher when:
        # 1. Memory strength is low (need to review)
        # 2. Success rate is low (need practice)
        # 3. Time since last review is close to optimal interval
        priority = (
            (1 - memory_strength) * 0.5 +  # Memory decay component
            (1 - success_rate/100) * 0.3 +     # Success rate component
            (abs(hours_since_last - optimal_interval) / optimal_interval) * 0.2  # Timing component
        )
        
        # Add a small random factor to avoid getting stuck in patterns
        priority += random.uniform(0, 0.1)
        
        return priority

    def select_word(self):
        """Select the next word to learn based on priority."""
        if len(self.vocabulary) == 0:
            return None

        # First, look for words that haven't been practiced yet
        new_words = self.vocabulary[~self.vocabulary['japanese'].isin(self.progress.keys())]
        if not new_words.empty:
            # Return the first new word (maintaining order)
            return new_words.iloc[0]

        # If all words have been practiced at least once, use the priority system
        word_priorities = []
        for _, row in self.vocabulary.iterrows():
            japanese_word = row['japanese']
            word_data = self.progress.get(japanese_word)
            priority = self.calculate_priority(word_data)
            word_priorities.append((japanese_word, priority))

        # Sort by priority and add some randomness
        word_priorities.sort(key=lambda x: x[1] + random.random() * 0.2, reverse=True)
        selected_word = word_priorities[0][0]
        
        return self.vocabulary[self.vocabulary['japanese'] == selected_word].iloc[0]

    def update_progress(self, word, success):
        """Update progress for a given word and sync with Firebase."""
        if word not in self.progress:
            self.progress[word] = {
                'attempts': 0,
                'successes': 0,
                'last_seen': datetime.now().isoformat(),
                'review_intervals': [],
                'last_attempt_was_failure': False
            }

        # Calculate and store interval since last review
        last_seen = datetime.fromisoformat(self.progress[word]['last_seen'])
        hours_since_last = (datetime.now() - last_seen).total_seconds() / 3600.0
        self.progress[word]['review_intervals'].append(hours_since_last)
        
        # Keep only last 10 intervals to track progress
        if len(self.progress[word]['review_intervals']) > 10:
            self.progress[word]['review_intervals'] = self.progress[word]['review_intervals'][-10:]

        self.progress[word]['attempts'] += 1
        if success:
            self.progress[word]['successes'] += 1
        self.progress[word]['last_seen'] = datetime.now().isoformat()
        
        # Save progress immediately after update
        self.save_progress()
        self.last_save_time = datetime.now()

    def show_save_status(self):
        """Show the current save status and statistics."""
        table = Table(title="Save Status")
        table.add_column("Information", style="bold")
        table.add_column("Value", style="green")

        # Get save file info
        save_file = Path(self.progress_file)
        file_exists = save_file.exists()
        
        if file_exists:
            file_size = save_file.stat().st_size
            last_modified = datetime.fromtimestamp(save_file.stat().st_mtime)
            seconds_since_save = (datetime.now() - self.last_save_time).total_seconds()
            
            table.add_row("Auto-save Status", "Active (saves after each answer)")
            table.add_row("Last Save", f"{seconds_since_save:.1f} seconds ago")
            table.add_row("Save File", self.progress_file)
            table.add_row("File Size", f"{file_size / 1024:.1f} KB")
            table.add_row("Words Tracked", str(len(self.progress)))
            table.add_row("Last Modified", last_modified.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            table.add_row("Auto-save Status", "[red]No save file found[/red]")
            table.add_row("Save File", self.progress_file)
            table.add_row("Words Tracked", "0")

        self.console.print(table)

    def show_help(self):
        """Display Vim-like commands help."""
        table = Table(title="Available Commands")
        table.add_column("Command", style="bold")
        table.add_column("Description", style="green")
        
        for cmd, desc in self.vim_commands.items():
            table.add_row(cmd, desc)
            
        self.console.print(table)

    def romaji_to_hiragana_convert(self, text):
        """Convert romaji to hiragana using mapping."""
        text = text.lower()
        # Try direct mapping first
        if text in self.romaji_to_hiragana:
            return self.romaji_to_hiragana[text]
        
        # If not found, try to convert character by character
        result = ''
        i = 0
        while i < len(text):
            # Try to match longest possible substring
            found = False
            for length in range(min(4, len(text) - i + 1), 0, -1):
                substr = text[i:i+length]
                if substr in self.romaji_to_hiragana:
                    result += self.romaji_to_hiragana[substr]
                    i += length
                    found = True
                    break
            if not found:
                # If no match found, keep the original character
                result += text[i]
                i += 1
        return result

    def convert_japanese_text(self, text):
        """Convert Japanese text between different writing systems."""
        try:
            # Check if input is romaji
            is_romaji = all(c in 'abcdefghijklmnopqrstuvwxyz ' for c in text.lower())
            
            if is_romaji:
                # Convert romaji to hiragana first
                hiragana = self.romaji_to_hiragana_convert(text)
                # Then use kakasi for other conversions
                result = self.kks.convert(hiragana)
            else:
                result = self.kks.convert(text)
            
            # Create conversion results
            conversions = {
                'hiragana': hiragana if is_romaji else ''.join([item['hira'] for item in result]),
                'katakana': ''.join([item['kana'] for item in result]),
                'romaji': text if is_romaji else ''.join([item['hepburn'] for item in result])
            }
            
            # If input contains kanji, store it
            if any(ord(char) >= 0x4E00 and ord(char) <= 0x9FFF for char in text):
                conversions['kanji'] = text
            else:
                # Try to get kanji suggestion from translator
                try:
                    kanji_suggestion = self.translator.translate(
                        conversions['hiragana'], src='ja', dest='ja'
                    ).text
                    if any(ord(char) >= 0x4E00 and ord(char) <= 0x9FFF for char in kanji_suggestion):
                        conversions['kanji'] = kanji_suggestion
                    else:
                        conversions['kanji'] = ''
                except:
                    conversions['kanji'] = ''
            
            return conversions
        except Exception as e:
            self.console.print(f"[yellow]Warning: Error in text conversion: {str(e)}[/yellow]")
            return {
                'hiragana': text,
                'katakana': text,
                'romaji': text,
                'kanji': ''
            }

    def suggest_translation(self, text, source_lang='ja', target_lang='fr'):
        """Get translation suggestion using Google Translate."""
        try:
            translation = self.translator.translate(text, src=source_lang, dest=target_lang)
            return translation.text
        except Exception as e:
            self.console.print(f"[yellow]Translation service unavailable: {str(e)}[/yellow]")
            return None

    def add_vocabulary(self):
        """Add new vocabulary interactively."""
        print("\nAdd New Vocabulary")
        print("Enter 'q' to return to menu")
        
        while True:
            # Get Japanese word
            japanese = input("\nEnter Japanese word (hiragana): ").strip()
            if japanese.lower() == 'q':
                break
            
            # Get kanji (optional)
            kanji = input("Enter kanji (optional): ").strip()
            if kanji.lower() == 'q':
                break
            
            # Get French translation
            french = input("Enter French translation: ").strip()
            if french.lower() == 'q':
                break
            
            # Get example sentence (optional)
            example = input("Enter example sentence (optional): ").strip()
            if example.lower() == 'q':
                break
            
            # Validate input
            if not japanese or not french:
                self.console.print("[red]Japanese word and French translation are required![/red]")
                continue
            
            # Check for duplicates
            if any(self.vocabulary['japanese'].str.lower() == japanese.lower()):
                self.console.print("[red]This word already exists![/red]")
                continue
            
            try:
                # Get the next word ID
                next_id = 1
                if os.path.exists(self.vocab_file):
                    with open(self.vocab_file, 'r', encoding='utf-8') as f:
                        vocab_data = json.load(f)
                        if vocab_data:
                            next_id = max(int(word_id.split('_')[1]) for word_id in vocab_data.keys()) + 1
                else:
                    vocab_data = {}
                
                # Create new word entry
                new_word = {
                    f"word_{str(next_id).zfill(6)}": {
                        "hiragana": japanese,
                        "kanji": kanji if kanji else "",
                        "french": french,
                        "example_sentence": example if example else ""
                    }
                }
                
                # Update vocabulary data
                vocab_data.update(new_word)
                
                # Save to JSON file
                with open(self.vocab_file, 'w', encoding='utf-8') as f:
                    json.dump(vocab_data, f, ensure_ascii=False, indent=2)
                
                # Update DataFrame
                self.load_vocabulary()
                
                # Sync to Firebase if available
                if self.vocab_ref is not None:
                    try:
                        self.vocab_ref.set(vocab_data)
                        self.console.print("[green]✓ Word added and synced to Firebase![/green]")
                    except Exception as e:
                        self.console.print(f"[yellow]Word added locally but failed to sync to Firebase: {str(e)}[/yellow]")
                else:
                    self.console.print("[green]✓ Word added successfully![/green]")
                
            except Exception as e:
                self.console.print(f"[red]Error adding word: {str(e)}[/red]")
                continue
            
            if not Confirm.ask("Add another word?"):
                break

    def normalize_french(self, text):
        """Remove accents and normalize French text."""
        # Convert to lowercase and strip
        text = text.lower().strip()
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        # Remove diacritics
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text

    def _is_minor_typo(self, str1, str2, threshold=0.85):
        """Check if two strings are similar enough to be considered a typo."""
        return SequenceMatcher(None, str1, str2).ratio() > threshold

    def check_answer(self, user_answer, correct_answer):
        """Check if the answer is correct, handling multiple possible answers and typos."""
        user_answer = user_answer.lower().strip()
        # Split correct answer by slashes and clean each part
        correct_answers = [ans.strip() for ans in correct_answer.split('/')]
        
        # First try exact match with any of the possible answers
        if any(user_answer == ans.lower() for ans in correct_answers):
            # If there are multiple answers, show them all after success
            if len(correct_answers) > 1:
                formatted_answers = ' / '.join(f"[green]{ans}[/green]" for ans in correct_answers)
                return True, f"[yellow]Note: Any of these answers would be correct: {formatted_answers}[/yellow]"
            return True, None
            
        # Then try normalized match (without accents) and typo detection
        user_normalized = self.normalize_french(user_answer)
        
        # First check for exact matches without accents
        for ans in correct_answers:
            ans_normalized = self.normalize_french(ans)
            if user_normalized == ans_normalized:
                return False, f"[yellow]Almost! You wrote '{user_answer}' but the correct spelling is '{ans}'[/yellow]"
        
        # Then check for typos, including in phrases
        for ans in correct_answers:
            ans_normalized = self.normalize_french(ans)
            # For phrases, check if all words are close matches
            if ' ' in user_normalized and ' ' in ans_normalized:
                user_words = user_normalized.split()
                ans_words = ans_normalized.split()
                if len(user_words) == len(ans_words) and all(
                    self._is_minor_typo(uw, aw) for uw, aw in zip(user_words, ans_words)
                ):
                    if Confirm.ask(f"\n[yellow]Did you mean '[green]{ans}[/green]'? Count as correct?[/yellow]"):
                        if len(correct_answers) > 1:
                            formatted_answers = ' / '.join(f"[green]{a}[/green]" for a in correct_answers)
                            return True, f"[yellow]Noted! The correct spelling is '{ans}'\nAny of these answers would be correct: {formatted_answers}[/yellow]"
                        return True, f"[yellow]Noted! The correct spelling is '[green]{ans}[/green]'[/yellow]"
            # For single words, check as before
            elif self._is_minor_typo(user_normalized, ans_normalized):
                if Confirm.ask(f"\n[yellow]Did you mean '[green]{ans}[/green]'? Count as correct?[/yellow]"):
                    if len(correct_answers) > 1:
                        formatted_answers = ' / '.join(f"[green]{a}[/green]" for a in correct_answers)
                        return True, f"[yellow]Noted! The correct spelling is '{ans}'\nAny of these answers would be correct: {formatted_answers}[/yellow]"
                    return True, f"[yellow]Noted! The correct spelling is '[green]{ans}[/green]'[/yellow]"
        
        return False, None

    def show_word_statistics(self, word_pair):
        """Display statistics for a specific word."""
        table = Table(title=f"Statistics for {word_pair['japanese']}")
        table.add_column("Information", style="bold")
        table.add_column("Value", style="green")

        stats = self.progress.get(word_pair['japanese'], {
            'attempts': 0,
            'successes': 0,
            'last_seen': 'Never',
            'review_intervals': []
        })

        success_rate = (stats['successes'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0
        last_seen = stats['last_seen']
        if last_seen != 'Never':
            last_seen_date = datetime.fromisoformat(last_seen)
            days_ago = (datetime.now() - last_seen_date).days
            if days_ago == 0:
                last_seen = "Today"
            elif days_ago == 1:
                last_seen = "Yesterday"
            else:
                last_seen = f"{days_ago} days ago"

        # Calculate average interval between reviews
        intervals = stats.get('review_intervals', [])
        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        table.add_row("Japanese", word_pair['japanese'])
        if pd.notna(word_pair['kanji']) and word_pair['kanji']:
            table.add_row("Kanji", word_pair['kanji'])
        table.add_row("French", word_pair['french'])
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Total Attempts", str(stats['attempts']))
        table.add_row("Successful Attempts", str(stats['successes']))
        table.add_row("Failed Attempts", str(stats['attempts'] - stats['successes']))
        table.add_row("Last Practice", last_seen)
        if avg_interval > 0:
            if avg_interval < 24:
                table.add_row("Average Review Interval", f"{avg_interval:.1f} hours")
            else:
                table.add_row("Average Review Interval", f"{avg_interval/24:.1f} days")

        self.console.print(table)

    def practice(self):
        """Practice mode for vocabulary learning."""
        if len(self.vocabulary) == 0:
            self.console.print("[yellow]No vocabulary words available. Please add some words to the vocabulary.[/yellow]")
            return
        
        self.console.print("\n[bold]Practice Mode[/bold]\n")
        self.console.print("[dim]Available commands:[/dim]")
        self.console.print("[blue]:h[/blue] help • [blue]:m[/blue] menu • [blue]:q[/blue] quit • [blue]:s[/blue] show progress • [blue]:d[/blue] don't know")
        
        while True:
            # Select a word to practice
            word_pair = self.select_word()
            if word_pair is None:
                self.console.print("[yellow]No vocabulary words available.[/yellow]")
                break
            
            # Display the word
            japanese = word_pair['japanese']
            kanji = word_pair['kanji'] if pd.notna(word_pair['kanji']) else None
            french = word_pair['french']
            example = word_pair['example_sentence'] if pd.notna(word_pair['example_sentence']) else None
            
            # Track if this is the first attempt for progress tracking
            first_attempt = True
            got_it_right = False
            
            while not got_it_right:
                # Show the Japanese word (with kanji if available)
                if kanji:
                    self.console.print(f"\n[bold cyan][Q][/bold cyan] {japanese} [[bold magenta]{kanji}[/bold magenta]]")
                else:
                    self.console.print(f"\n[bold cyan][Q][/bold cyan] {japanese}")
                
                # Get user's answer
                while True:
                    answer = input("Your answer: ").strip()
                    
                    # Handle commands
                    if answer.startswith(':'):
                        if answer == ':q':
                            self.console.print("\n[yellow]Saving progress...[/yellow]")
                            self.save_progress()
                            return
                        elif answer == ':m':
                            return
                        elif answer == ':h':
                            self.show_help()
                            continue
                        elif answer == ':s':
                            self.show_word_statistics(word_pair)
                            continue
                        elif answer == ':e' and example:
                            self.console.print(f"\n[bold]Example:[/bold] {example}")
                            continue
                        elif answer == ':d':
                            print("\033[A", end="")  # Move cursor up one line
                            print("\033[2K", end="")  # Clear the line
                            self.console.print(f"Your answer: :d    [bold red]✗ Don't know[/bold red]")
                            self.console.print(f"The correct answer is: [green]{french}[/green]")
                            if first_attempt:
                                self.update_progress(japanese, False)
                            got_it_right = True  # Move to next word after showing answer
                            break
                        else:
                            self.console.print("[red]Invalid command. Type :h for help.[/red]")
                            continue
                    
                    # Check the answer
                    is_correct, message = self.check_answer(answer, french)
                    if is_correct:
                        print("\033[A", end="")  # Move cursor up one line
                        print("\033[2K", end="")  # Clear the line
                        self.console.print(f"Your answer: {answer}    [bold green]✓ Correct![/bold green]")
                        if message:
                            self.console.print(message)
                        if first_attempt:
                            self.update_progress(japanese, True)
                        got_it_right = True
                        break
                    else:
                        print("\033[A", end="")  # Move cursor up one line
                        print("\033[2K", end="")  # Clear the line
                        self.console.print(f"Your answer: {answer}    [bold red]✗ Incorrect[/bold red]")
                        self.console.print(f"The correct answer is: [green]{french}[/green]")
                        if message:
                            self.console.print(message)
                        if first_attempt:
                            self.update_progress(japanese, False)
                        first_attempt = False
                        self.console.print("\n[yellow]Let's try again![/yellow]")
                        break
            
            # Auto-save progress periodically
            if (datetime.now() - self.last_save_time).seconds > 300:  # 5 minutes
                self.save_progress()
                self.last_save_time = datetime.now()
            
            self.console.print()  # Just add a newline for spacing

    def reset_progress(self):
        """Reset all learning progress."""
        if Confirm.ask("[red]Are you sure you want to reset all progress?[/red] This cannot be undone"):
            # Backup current progress
            if os.path.exists(self.progress_file):
                backup_file = f"{self.progress_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    with open(self.progress_file, 'r', encoding='utf-8') as src, \
                         open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                    self.console.print(f"[dim]Progress backed up to: {backup_file}[/dim]")
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Could not create backup: {str(e)}[/yellow]")
            
            # Reset progress
            self.progress = {}
            self.save_progress()
            
            # Reset Firebase if available
            firebase_status = ""
            if self.progress_ref is not None:
                try:
                    self.progress_ref.set({})
                    firebase_status = " and Firebase"
                except Exception as e:
                    firebase_status = f" (Firebase reset failed: {str(e)})"
            
            self.console.print(f"[green]Progress reset successfully{firebase_status}![/green]")
        else:
            self.console.print("[dim]Progress reset cancelled[/dim]")

def main():
    console = Console()
    console.print("\n[bold blue]=== Japanese Vocabulary Learning Tool ===[/bold blue]")
    
    learner = VocabularyLearner()
    
    # Start with practice mode
    learner.practice()
    
    while True:
        console.print("\n[bold]Main Menu[/bold]")
        console.print("[purple]1.[/purple] Practice vocabulary")
        console.print("[purple]2.[/purple] Show progress")
        console.print("[purple]3.[/purple] Add vocabulary")
        console.print("[purple]4.[/purple] Reset progress")
        console.print("[blue]:q[/blue] Quit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == '1':
            learner.practice()
        elif choice == '2':
            learner.show_progress()
            if not Confirm.ask("\nReturn to menu?"):
                break
        elif choice == '3':
            learner.add_vocabulary()
        elif choice == '4':
            learner.reset_progress()
        elif choice == ':q':
            console.print("\n[yellow]Saving progress...[/yellow]")
            learner.save_progress()
            console.print("[green]Goodbye![/green]")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
        sys.exit(0)