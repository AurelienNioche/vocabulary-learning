"""Practice mode functionality for vocabulary learning."""

import random
from datetime import datetime

import pandas as pd
from rich.console import Console
from rich.prompt import Confirm

from vocabulary_learning.core.progress_tracking import (
    calculate_priority,
    count_active_learning_words,
)
from vocabulary_learning.core.utils import (
    exit_with_save,
    format_multiple_answers,
    is_minor_typo,
    normalize_french,
    show_answer_feedback,
    update_progress_if_first_attempt,
)


def practice_mode(
    vocabulary,
    progress,
    console,
    japanese_converter,
    update_progress_fn,
    show_help_fn,
    show_word_stats_fn,
    save_progress_fn,
):
    """Practice mode for vocabulary learning."""
    if len(vocabulary) == 0:
        console.print(
            "[yellow]No vocabulary words found. Please add some words to the vocabulary.[/yellow]"
        )
        return

    console.print("\n[bold]Practice Mode[/bold]\n")

    # Verify progress data
    mastered_count = 0
    active_count = 0
    for word_data in progress.values():
        attempts = word_data.get("attempts", 0)
        successes = word_data.get("successes", 0)
        if attempts > 0:
            success_rate = successes / attempts
            if success_rate >= 0.9 and successes >= 5:
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
        "[blue]:h[/blue] help • [blue]:m[/blue] menu • [blue]:q[/blue] quit • [blue]:s[/blue] show progress • [blue]:d[/blue] don't know • [blue]:e[/blue] show example"
    )

    last_save_time = datetime.now()

    while True:
        # Select a word to practice
        word_pair = select_word(vocabulary, progress)
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
        example = word_pair["example_sentence"] if pd.notna(word_pair["example_sentence"]) else None

        # Track if this is the first attempt for progress tracking
        first_attempt = True
        got_it_right = False

        while not got_it_right:
            # Show the Japanese word (with kanji if available)
            if kanji:
                console.print(
                    f"\n[bold cyan][Q][/bold cyan] {japanese} [[bold magenta]{kanji}[/bold magenta]]"
                )
            else:
                console.print(f"\n[bold cyan][Q][/bold cyan] {japanese}")

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
                        console.print(f"Your answer: :d    [bold red]✗ Don't know[/bold red]")
                        console.print(f"The correct answer is: [green]{french}[/green]")
                        console.print("\n[yellow]Let's try again![/yellow]")
                        if first_attempt:
                            update_progress_fn(japanese, False)
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
                        update_progress_fn, japanese, True, first_attempt
                    )
                    got_it_right = True
                    break
                else:
                    show_answer_feedback(console, answer, False, message)
                    console.print(f"The correct answer is: [green]{french}[/green]")
                    update_progress_if_first_attempt(
                        update_progress_fn, japanese, False, first_attempt
                    )
                    first_attempt = False
                    console.print("\n[yellow]Let's try again![/yellow]")
                    break

        # Auto-save progress periodically
        if (datetime.now() - last_save_time).seconds > 300:  # 5 minutes
            save_progress_fn()
            last_save_time = datetime.now()

        console.print()  # Just add a newline for spacing


def select_word(vocabulary, progress):
    """Select the next word to practice based on priority and active word limit.

    Args:
        vocabulary: DataFrame containing vocabulary words
        progress: Dictionary containing progress data for each word

    Returns:
        Selected word as a DataFrame row, or None if no word is available
    """
    if len(vocabulary) == 0:
        return None

    # Count active learning words
    active_words_count = count_active_learning_words(progress)

    # Calculate priorities for all words in progress
    word_priorities = []
    for _, row in vocabulary.iterrows():
        japanese_word = row["japanese"]
        if japanese_word in progress:
            word_data = progress[japanese_word]
            # Skip mastered words
            attempts = word_data.get("attempts", 0)
            successes = word_data.get("successes", 0)
            if attempts > 0:
                success_rate = successes / attempts
                if success_rate >= 0.9 and successes >= 5:
                    continue

            priority = calculate_priority(word_data, active_words_count)
            if priority > 0:  # Only add words that are ready for review
                word_priorities.append((japanese_word, priority))

    # If we have words in progress that need review, prioritize them
    if word_priorities:
        word_priorities.sort(key=lambda x: x[1] + random.random() * 0.1, reverse=True)
        selected_word = word_priorities[0][0]
        selected_priority = word_priorities[0][1]
        selected = vocabulary[vocabulary["japanese"] == selected_word].iloc[0]
        word_data = progress[selected_word]

        # Calculate success rate
        attempts = word_data.get("attempts", 0)
        successes = word_data.get("successes", 0)
        success_rate = (successes / attempts * 100) if attempts > 0 else 0

        console = Console()
        console.print(f"\n[dim]Selecting word {selected_word}[/dim]")
        console.print(f"[dim]- priority: {selected_priority:.4f}[/dim]")
        console.print(f"[dim]- success rate: {success_rate:.1f}% ({successes}/{attempts})[/dim]")
        console.print(f"[dim]- easiness factor: {word_data.get('easiness_factor', 2.5):.2f}[/dim]")
        console.print(f"[dim]- current interval: {word_data.get('interval', 0):.2f} hours[/dim]")
        console.print(
            f"[dim]- last attempt was a success: {not word_data.get('last_attempt_was_failure', False)}[/dim]"
        )
        return selected

    # If no words are ready for review, look for new words
    new_words = vocabulary[~vocabulary["japanese"].isin(progress.keys())]
    if not new_words.empty:
        # Return the first new word (maintaining order)
        selected = new_words.iloc[0]
        console = Console()
        console.print(f"\n[dim]Selecting word {selected['japanese']}[/dim]")
        console.print("[dim]- priority: 0.8000 (new word)[/dim]")
        console.print("[dim]- success rate: 0.0% (0/0)[/dim]")
        console.print("[dim]- easiness factor: 2.50 (initial)[/dim]")
        console.print("[dim]- current interval: 0.00 hours[/dim]")
        console.print("[dim]- last attempt was a success: True[/dim]")
        return selected

    return None


def check_answer(user_answer, correct_answer):
    """Check if the answer is correct, handling multiple possible answers and typos."""
    user_answer = user_answer.lower().strip()
    # Split correct answer by slashes and clean each part
    correct_answers = [ans.strip() for ans in correct_answer.split("/")]

    # First try exact match with any of the possible answers
    if any(user_answer == ans.lower() for ans in correct_answers):
        # If there are multiple answers, show them all after success
        if len(correct_answers) > 1:
            formatted_answers = format_multiple_answers(correct_answers)
            return (
                True,
                f"[yellow]Note: Any of these answers would be correct: {formatted_answers}[/yellow]",
            )
        return True, None

    # Then try normalized match (without accents) and typo detection
    user_normalized = normalize_french(user_answer)

    # First check for exact matches without accents
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        if user_normalized == ans_normalized:
            return (
                False,
                f"[yellow]Almost! You wrote '{user_answer}' but the correct spelling is '{ans}'[/yellow]",
            )

    # Then check for typos, including in phrases
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        # For phrases, check if all words are close matches
        if " " in user_normalized and " " in ans_normalized:
            user_words = user_normalized.split()
            ans_words = ans_normalized.split()
            if len(user_words) == len(ans_words) and all(
                is_minor_typo(uw, aw) for uw, aw in zip(user_words, ans_words)
            ):
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
        # For single words, check as before
        elif is_minor_typo(user_normalized, ans_normalized):
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
