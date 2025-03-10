"""Practice mode functionality for vocabulary learning."""

import os
from datetime import datetime
from typing import Dict

import pandas as pd
import pytz
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm

from vocabulary_learning.core.console_utils import (
    exit_with_save,
    format_multiple_answers,
    show_answer_feedback,
)
from vocabulary_learning.core.constants import (
    DEFAULT_TIMEZONE,
    INITIAL_EASINESS_FACTOR,
    MASTERY_MIN_SUCCESSES,
    MASTERY_SUCCESS_RATE,
    REQUIRED_PROGRESS_FIELDS,
    REQUIRED_VOCABULARY_COLUMNS,
    VIM_COMMANDS,
    WORD_ID_DIGITS,
)
from vocabulary_learning.core.progress_helpers import update_progress_if_first_attempt
from vocabulary_learning.core.progress_tracking import (
    calculate_priority,
    calculate_weighted_success_rate,
    count_active_learning_words,
    is_mastered,
)
from vocabulary_learning.core.text_processing import (
    format_datetime,
    format_time_interval,
    is_minor_typo,
    normalize_french,
)

# Load timezone from .env
load_dotenv()
TIMEZONE = os.getenv(
    "TIMEZONE", DEFAULT_TIMEZONE
)  # Default to DEFAULT_TIMEZONE if not set
try:
    tz = pytz.timezone(TIMEZONE)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"Warning: Unknown timezone {TIMEZONE}, falling back to UTC")
    tz = pytz.UTC


def practice_mode(
    vocabulary,
    progress,
    console,
    japanese_converter,
    update_progress_fn,
    show_help_fn,
    show_word_stats_fn,
    save_progress_fn,
    initialize_progress_fn,
):
    """Practice mode for vocabulary learning."""
    if len(vocabulary) == 0:
        console.print(
            "[yellow]No vocabulary words found. Please add some words to the vocabulary.[/yellow]"
        )
        return

    console.print("\n[bold]Practice Mode[/bold]\n")
    start_time = datetime.now()
    question_counter = 1

    # Verify progress data
    mastered_count = 0
    active_count = 0
    for word_data in progress.values():
        attempts = word_data.get("attempts", 0)
        successes = word_data.get("successes", 0)
        if attempts > 0:
            success_rate = successes / attempts
            if (
                success_rate >= MASTERY_SUCCESS_RATE
                and successes >= MASTERY_MIN_SUCCESSES
            ):
                mastered_count += 1
            else:
                active_count += 1

    # Print initial statistics
    console.print(f"[dim]Total number of words: {len(vocabulary)}[/dim]")
    console.print(f"[dim]Number of words in progress: {len(progress)}[/dim]")
    console.print(f"[dim]Active learning words count: {active_count}[/dim]")
    console.print(f"[dim]Mastered words count: {mastered_count}[/dim]")
    console.print(
        f"[dim]Vocabulary data verification: {all(isinstance(row['japanese'], str) and isinstance(row['french'], str) for _, row in vocabulary.iterrows())}[/dim]"
    )
    console.print(
        f"[dim]Progress data verification: {all(isinstance(p, dict) for p in progress.values())}[/dim]\n"
    )

    console.print("[dim]Available commands:[/dim]")
    console.print(
        " • ".join(f"[blue]{cmd}[/blue] {desc}" for cmd, desc in VIM_COMMANDS.items())
    )

    while True:
        # Display elapsed time
        elapsed_time = datetime.now() - start_time
        total_seconds = int(elapsed_time.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if minutes == 0:
            console.print(f"\n[dim]Time elapsed: {seconds}s[/dim]")
        else:
            console.print(f"\n[dim]Time elapsed: {minutes}min{seconds}s[/dim]")

        # Select a word to practice
        word_pair = select_word(vocabulary, progress, console, initialize_progress_fn)
        if word_pair is None:
            active_count = count_active_learning_words(progress)
            console.print(
                f"[yellow]You currently have {active_count} active words.[/yellow]\n"
                "[yellow]No words are ready for review right now. Try again later![/yellow]"
            )
            break

        # Display the word
        japanese = word_pair["japanese"]
        kanji = word_pair["kanji"] if pd.notna(word_pair["kanji"]) else None
        french = word_pair["french"]
        example = (
            word_pair["example_sentence"]
            if pd.notna(word_pair["example_sentence"])
            else None
        )

        # Get word ID for progress tracking
        word_index = vocabulary[vocabulary["japanese"] == japanese].index[0]
        word_id = str(word_index + 1).zfill(WORD_ID_DIGITS)

        # Track if this is the first attempt for progress tracking
        first_attempt = True
        got_it_right = False

        while not got_it_right:
            # Show the Japanese word (with kanji if available)
            if kanji:
                console.print(
                    f"\n[bold cyan][Q{question_counter}][/bold cyan] {japanese} [[bold magenta]{kanji}[/bold magenta]]"
                )
            else:
                console.print(
                    f"\n[bold cyan][Q{question_counter}][/bold cyan] {japanese}"
                )

            # Get user's answer
            while True:
                answer = input("Your answer: ").strip()

                # Handle commands
                if answer.startswith(":"):
                    if answer == ":q":
                        exit_with_save(save_progress_fn, console)
                    elif answer == ":m":
                        return
                    elif answer == ":h":
                        show_help_fn()
                        continue
                    elif answer == ":s":
                        show_word_stats_fn(word_pair)
                        continue
                    elif answer == ":e" and example:
                        # Convert example to hiragana
                        result = japanese_converter.kks.convert(example)
                        hiragana = "".join([item["hira"] for item in result])
                        console.print(f"\n[bold]Example:[/bold] {hiragana} / {example}")
                        continue
                    elif answer == ":d":
                        print("\033[A", end="")  # Move cursor up one line
                        print("\033[2K", end="")  # Clear the line
                        console.print(
                            "Your answer: :d    [bold red]✗ Don't know[/bold red]"
                        )
                        console.print(
                            f"The correct answer is: [green]{french}[/green]\n"
                        )

                        # Update progress only on first attempt
                        if first_attempt:
                            update_progress_if_first_attempt(
                                update_progress_fn, word_id, False, first_attempt
                            )
                            # Show updated stats if this is the first attempt
                            if word_id in progress:
                                display_updated_stats(
                                    progress[word_id],
                                    japanese,
                                    word_id,
                                    active_count,
                                    console,
                                )

                        console.print("\n[yellow]Let's try again![/yellow]")
                        first_attempt = False
                        got_it_right = False
                        break
                    else:
                        console.print("[red]Invalid command. Type :h for help.[/red]")
                        continue

                # Check the answer
                is_correct, message = check_answer(answer, french)
                if is_correct:
                    show_answer_feedback(console, answer, True, message)
                    update_progress_if_first_attempt(
                        update_progress_fn, word_id, True, first_attempt
                    )
                    got_it_right = True
                    # Show updated stats
                    if first_attempt and word_id in progress:
                        display_updated_stats(
                            progress[word_id], japanese, word_id, active_count, console
                        )
                    break
                else:
                    show_answer_feedback(console, answer, False, message)
                    console.print(f"The correct answer is: [green]{french}\n")
                    # Show updated stats if this is the first attempt
                    if first_attempt and word_id in progress:
                        update_progress_if_first_attempt(
                            update_progress_fn, word_id, False, first_attempt
                        )
                        display_updated_stats(
                            progress[word_id], japanese, word_id, active_count, console
                        )
                    else:
                        # Display stats without updating progress
                        if word_id in progress:
                            display_updated_stats(
                                progress[word_id],
                                japanese,
                                word_id,
                                active_count,
                                console,
                            )
                        else:
                            console.print(
                                f"\n[yellow]No progress data for word {word_id}[/yellow]"
                            )
                    first_attempt = False
                    console.print("\n[yellow]Let's try again![/yellow]")
                    break

        # Only increment question counter when moving to a new word
        if got_it_right:
            question_counter += 1
            console.print(
                "\n[dim]• ─────────────────────── •[/dim]"
            )  # Add decorative separator


def verify_data(vocabulary: pd.DataFrame, progress: Dict) -> None:
    """Verify the integrity of vocabulary and progress data.

    Args:
        vocabulary: DataFrame containing vocabulary
        progress: Dictionary containing progress data
    """
    # Verify vocabulary has required columns
    for column in REQUIRED_VOCABULARY_COLUMNS:
        if column not in vocabulary.columns:
            raise ValueError(f"Missing required column: {column}")

    # Verify progress data structure
    for word_id, word_data in progress.items():
        for field in REQUIRED_PROGRESS_FIELDS:
            if field not in word_data:
                raise ValueError(
                    f"Missing required field {field} in progress data for {word_id}"
                )


def select_word(
    vocabulary: pd.DataFrame,
    progress: Dict,
    console: Console,
    initialize_progress_fn=None,
) -> pd.Series:
    """Select a word for practice based on priority.

    Args:
        vocabulary: DataFrame containing vocabulary words
        progress: Dictionary containing progress data
        console: Console for output
        initialize_progress_fn: Function to initialize progress for a word

    Returns
    -------
        Selected word as a pandas Series
    """
    # Verify data integrity
    verify_data(vocabulary, progress)

    # Count active learning words
    active_words_count = count_active_learning_words(progress)

    # Get new words (not in progress)
    progress_word_ids = set(progress.keys())
    new_words = vocabulary[
        ~vocabulary.index.isin(
            [
                i
                for i in range(len(vocabulary))
                if str(i + 1).zfill(WORD_ID_DIGITS) in progress_word_ids
            ]
        )
    ]

    # Calculate priorities for words in progress
    priorities = {}
    max_priority = 0.0
    for word_id, word_data in progress.items():
        if not is_mastered(word_data):
            priority = calculate_priority(word_data, active_words_count)
            priorities[word_id] = priority
            max_priority = max(max_priority, priority)

    # Calculate priority for new words
    new_word_priority = calculate_priority(None, active_words_count)

    # If new words have higher priority than existing words, select a new word
    if new_word_priority > max_priority and not new_words.empty:
        selected_word = new_words.iloc[0]
        word_id = str(selected_word.name + 1).zfill(WORD_ID_DIGITS)

        # Initialize progress for this new word
        if initialize_progress_fn:
            initialize_progress_fn(word_id)

        console.print(f"\n[dim]Selecting {selected_word['japanese']} [{word_id}][/dim]")
        console.print(f"[dim]- priority: {new_word_priority:.1f} (new word)[/dim]")
        console.print("[dim]- success rate: 0% (0/0)[/dim]")
        console.print(f"[dim]- easiness factor: {INITIAL_EASINESS_FACTOR}[/dim]")
        console.print("[dim]- optimal interval: as soon as possible[/dim]")
        console.print("[dim]- last attempt was a success: N/A[/dim]")
        console.print("[dim]- last presented: never[/dim]")
        console.print("[dim]- mastery status: Not started[/dim]")
        return selected_word

    # If there are words in progress with higher priority, select based on priority
    if priorities:
        # Sort by priority (highest first)
        sorted_words = sorted(priorities.items(), key=lambda x: x[1], reverse=True)
        word_id, priority = sorted_words[0]

        # Check if word_id exists in progress
        if word_id not in progress and initialize_progress_fn:
            # Initialize progress for this word without counting it as an attempt
            initialize_progress_fn(word_id)

        word_data = progress[word_id]

        # Find corresponding word in vocabulary
        word_index = int(word_id) - 1
        selected_word = vocabulary.iloc[word_index]

        # Calculate mastery criteria
        successes = word_data.get("successes", 0)
        weighted_success_rate = calculate_weighted_success_rate(
            word_data.get("attempt_history", [])
        )
        mastery_status = []
        if successes < MASTERY_MIN_SUCCESSES:
            mastery_status.append(
                f"needs more successful reviews (minimum {MASTERY_MIN_SUCCESSES})"
            )
        if weighted_success_rate < MASTERY_SUCCESS_RATE:
            mastery_status.append(
                f"needs higher success rate (current: {weighted_success_rate:.1%})"
            )

        # Print selection details
        console.print(f"\n[dim]Selecting {selected_word['japanese']} [{word_id}][/dim]")
        console.print(f"[dim]- priority: {priority:.1f}[/dim]")
        raw_success_rate = (
            (word_data["successes"] / word_data["attempts"] * 100)
            if word_data["attempts"] > 0
            else 0
        )
        weighted_success_rate = (
            calculate_weighted_success_rate(word_data.get("attempt_history", [])) * 100
        )
        console.print(
            f"[dim]- success rate: {raw_success_rate:.0f}% raw, {weighted_success_rate:.0f}% weighted ({word_data['successes']}/{word_data['attempts']})[/dim]"
        )
        console.print(
            f"[dim]- easiness factor: {word_data['easiness_factor']:.1f}[/dim]"
        )
        console.print(
            f"[dim]- optimal interval: {format_time_interval(word_data['interval'])}[/dim]"
        )
        console.print(
            f"[dim]- last attempt was a success: {'No' if word_data['last_attempt_was_failure'] else 'Yes'}[/dim]"
        )
        console.print(
            f"[dim]- last presented: {format_datetime(word_data['last_seen'])}[/dim]"
        )
        if mastery_status:
            console.print(f"[dim]- mastery status: {', '.join(mastery_status)}[/dim]")
        else:
            console.print("[dim]- mastery status: Ready for mastery![/dim]")

        return selected_word

    # If no words are available for practice, return None
    return None


def check_answer(user_answer, correct_answer):
    """Check if the answer is correct, handling multiple possible answers and typos."""
    user_answer = user_answer.lower().strip()
    # Split correct answer by slashes and clean each part
    correct_answers = [ans.strip().lower() for ans in correct_answer.split("/")]

    # First try exact match with any of the possible answers
    if any(user_answer == ans for ans in correct_answers):
        # If there are multiple answers, show them all after success
        if len(correct_answers) > 1:
            formatted_answers = format_multiple_answers(correct_answers)
            return (
                True,
                f"[dim]Note: Any of these answers would be correct: {formatted_answers}[/dim]",
            )
        return True, None

    # Then try normalized match (without accents)
    user_normalized = normalize_french(user_answer)
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        if user_normalized == ans_normalized:
            return (
                True,
                f"[yellow]Almost! You wrote '{user_answer}' but the correct spelling is '{ans}'[/yellow]",
            )

    # Then check for typos
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        if is_minor_typo(user_normalized, ans_normalized):
            if Confirm.ask(
                f"\n[yellow]Did you mean '[green]{ans}[/green]'? Count as correct?[/yellow]"
            ):
                if len(correct_answers) > 1:
                    formatted_answers = format_multiple_answers(correct_answers)
                    return (
                        True,
                        f"[yellow]Noted! The correct spelling is '{ans}'\nAny of these answers would be correct: {formatted_answers}[/yellow]",
                    )
                return (
                    True,
                    f"[yellow]Noted! The correct spelling is '[green]{ans}[/green]'[/yellow]",
                )

    return False, None


def display_word_stats(word_data, console):
    """Display word statistics."""
    console.print(f"[dim]- attempts: {word_data['attempts']}[/dim]")
    console.print(f"[dim]- successes: {word_data['successes']}[/dim]")
    console.print(f"[dim]- easiness factor: {word_data['easiness_factor']:.2f}[/dim]")
    console.print(
        f"[dim]- optimal interval: {format_time_interval(word_data['interval'])}[/dim]"
    )
    if "last_seen" in word_data:
        console.print(
            f"[dim]- last presented: {format_datetime(word_data['last_seen'])}[/dim]"
        )
    else:
        console.print("[dim]- last presented: never[/dim]")


def display_updated_stats(
    word_data: Dict, japanese: str, word_id: str, active_count: int, console: Console
) -> None:
    """Display updated statistics for a word after an attempt.

    Args:
        word_data: Dictionary containing word progress data
        japanese: Japanese word being practiced
        word_id: ID of the word
        active_count: Number of active words
        console: Rich console for output
    """
    raw_success_rate = (
        (word_data["successes"] / word_data["attempts"] * 100)
        if word_data["attempts"] > 0
        else 0
    )
    weighted_success_rate = (
        calculate_weighted_success_rate(word_data.get("attempt_history", [])) * 100
    )
    interval_text = format_time_interval(word_data["interval"])
    last_attempt_text = (
        "N/A"
        if word_data["attempts"] == 0
        else "yes"
        if not word_data["last_attempt_was_failure"]
        else "no"
    )
    last_seen = format_datetime(word_data["last_seen"])

    console.print(f"\n[dim]New stats for {japanese} [{word_id}]:[/dim]")
    priority = calculate_priority(word_data, active_count)
    console.print(f"[dim]- priority: {priority:.1f}[/dim]")
    console.print(
        f"[dim]- success rate: {raw_success_rate:.0f}% raw, {weighted_success_rate:.0f}% weighted ({word_data['successes']}/{word_data['attempts']})[/dim]"
    )
    console.print(f"[dim]- easiness factor: {word_data['easiness_factor']:.1f}[/dim]")
    console.print(f"[dim]- optimal interval: {interval_text}[/dim]")
    console.print(f"[dim]- last attempt was a success: {last_attempt_text}[/dim]")
    console.print(f"[dim]- last presented: {last_seen}[/dim]")

    # Add mastery status
    successes = word_data.get("successes", 0)
    weighted_success_rate = calculate_weighted_success_rate(
        word_data.get("attempt_history", [])
    )
    mastery_status = []
    if successes < MASTERY_MIN_SUCCESSES:
        mastery_status.append(
            f"needs more successful reviews (minimum {MASTERY_MIN_SUCCESSES})"
        )
    if weighted_success_rate < MASTERY_SUCCESS_RATE:
        mastery_status.append(
            f"needs higher success rate (current: {weighted_success_rate:.1%})"
        )

    if not mastery_status:  # If no criteria are failing
        console.print("[dim]- mastery status: [green]Mastered![/green][/dim]")
    else:
        console.print(
            f"[dim]- mastery status: Not mastered - {' and '.join(mastery_status)}[/dim]"
        )
