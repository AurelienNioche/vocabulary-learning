"""Practice mode functionality for vocabulary learning."""

import pandas as pd
import sys
from datetime import datetime
from rich.prompt import Confirm
import random
from vocabulary_learning.core.progress_tracking import count_active_learning_words, calculate_priority
from vocabulary_learning.core.utils import (
    normalize_french, is_minor_typo, exit_with_save, 
    show_answer_feedback, format_multiple_answers, 
    update_progress_if_first_attempt
)

def practice_mode(vocabulary, progress, console, japanese_converter, update_progress_fn, show_help_fn, show_word_stats_fn, save_progress_fn):
    """Practice mode for vocabulary learning."""
    if len(vocabulary) == 0:
        console.print("[yellow]No vocabulary words available. Please add some words to the vocabulary.[/yellow]")
        return
    
    console.print("\n[bold]Practice Mode[/bold]\n")
    console.print("[dim]Available commands:[/dim]")
    console.print("[blue]:h[/blue] help • [blue]:m[/blue] menu • [blue]:q[/blue] quit • [blue]:s[/blue] show progress • [blue]:d[/blue] don't know • [blue]:e[/blue] show example")
    
    last_save_time = datetime.now()
    
    while True:
        # Select a word to practice
        word_pair = select_word(vocabulary, progress)
        if word_pair is None:
            console.print("[yellow]No vocabulary words available.[/yellow]")
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
                console.print(f"\n[bold cyan][Q][/bold cyan] {japanese} [[bold magenta]{kanji}[/bold magenta]]")
            else:
                console.print(f"\n[bold cyan][Q][/bold cyan] {japanese}")
            
            # Get user's answer
            while True:
                answer = input("Your answer: ").strip()
                
                # Handle commands
                if answer.startswith(':'):
                    if answer == ':q':
                        exit_with_save(save_progress_fn, console)
                    elif answer == ':m':
                        return
                    elif answer == ':h':
                        show_help_fn()
                        continue
                    elif answer == ':s':
                        show_word_stats_fn(word_pair)
                        continue
                    elif answer == ':e' and example:
                        # Convert example to hiragana
                        result = japanese_converter.kks.convert(example)
                        hiragana = ''.join([item['hira'] for item in result])
                        console.print(f"\n[bold]Example:[/bold] {hiragana} / {example}")
                        continue
                    elif answer == ':d':
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
                    update_progress_if_first_attempt(update_progress_fn, japanese, True, first_attempt)
                    got_it_right = True
                    break
                else:
                    show_answer_feedback(console, answer, False, message)
                    console.print(f"The correct answer is: [green]{french}[/green]")
                    update_progress_if_first_attempt(update_progress_fn, japanese, False, first_attempt)
                    first_attempt = False
                    console.print("\n[yellow]Let's try again![/yellow]")
                    break
        
        # Auto-save progress periodically
        if (datetime.now() - last_save_time).seconds > 300:  # 5 minutes
            save_progress_fn()
            last_save_time = datetime.now()
        
        console.print()  # Just add a newline for spacing

def select_word(vocabulary, progress):
    """Select the next word to learn based on priority."""
    if len(vocabulary) == 0:
        return None

    # Count active learning words
    active_words_count = count_active_learning_words(progress)

    # First, look for words that haven't been practiced yet
    new_words = vocabulary[~vocabulary['japanese'].isin(progress.keys())]
    if not new_words.empty and active_words_count < 8:
        # Return the first new word (maintaining order)
        return new_words.iloc[0]

    # If all words have been practiced at least once, use the priority system
    word_priorities = []
    for _, row in vocabulary.iterrows():
        japanese_word = row['japanese']
        word_data = progress.get(japanese_word)
        priority = calculate_priority(word_data, active_words_count)
        word_priorities.append((japanese_word, priority))

    # Sort by priority and add some randomness
    word_priorities.sort(key=lambda x: x[1] + random.random() * 0.1, reverse=True)
    
    # Filter out words with zero priority (not due for review)
    valid_words = [(word, prio) for word, prio in word_priorities if prio > 0]
    
    if not valid_words:
        return None  # No words available for review
        
    selected_word = valid_words[0][0]
    return vocabulary[vocabulary['japanese'] == selected_word].iloc[0]

def check_answer(user_answer, correct_answer):
    """Check if the answer is correct, handling multiple possible answers and typos."""
    user_answer = user_answer.lower().strip()
    # Split correct answer by slashes and clean each part
    correct_answers = [ans.strip() for ans in correct_answer.split('/')]
    
    # First try exact match with any of the possible answers
    if any(user_answer == ans.lower() for ans in correct_answers):
        # If there are multiple answers, show them all after success
        if len(correct_answers) > 1:
            formatted_answers = format_multiple_answers(correct_answers)
            return True, f"[yellow]Note: Any of these answers would be correct: {formatted_answers}[/yellow]"
        return True, None
        
    # Then try normalized match (without accents) and typo detection
    user_normalized = normalize_french(user_answer)
    
    # First check for exact matches without accents
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        if user_normalized == ans_normalized:
            return False, f"[yellow]Almost! You wrote '{user_answer}' but the correct spelling is '{ans}'[/yellow]"
    
    # Then check for typos, including in phrases
    for ans in correct_answers:
        ans_normalized = normalize_french(ans)
        # For phrases, check if all words are close matches
        if ' ' in user_normalized and ' ' in ans_normalized:
            user_words = user_normalized.split()
            ans_words = ans_normalized.split()
            if len(user_words) == len(ans_words) and all(
                is_minor_typo(uw, aw) for uw, aw in zip(user_words, ans_words)
            ):
                if Confirm.ask(f"\n[yellow]Did you mean '[green]{ans}[/green]'? Count as correct?[/yellow]"):
                    if len(correct_answers) > 1:
                        formatted_answers = format_multiple_answers(correct_answers)
                        return True, f"[yellow]Noted! The correct spelling is '{ans}'\nAny of these answers would be correct: {formatted_answers}[/yellow]"
                    return True, f"[yellow]Noted! The correct spelling is '[green]{ans}[/green]'[/yellow]"
        # For single words, check as before
        elif is_minor_typo(user_normalized, ans_normalized):
            if Confirm.ask(f"\n[yellow]Did you mean '[green]{ans}[/green]'? Count as correct?[/yellow]"):
                if len(correct_answers) > 1:
                    formatted_answers = format_multiple_answers(correct_answers)
                    return True, f"[yellow]Noted! The correct spelling is '{ans}'\nAny of these answers would be correct: {formatted_answers}[/yellow]"
                return True, f"[yellow]Noted! The correct spelling is '[green]{ans}[/green]'[/yellow]"
    
    return False, None 