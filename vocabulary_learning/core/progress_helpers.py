"""Helper functions for progress tracking."""


def update_progress_if_first_attempt(
    update_fn, word_id: str, success: bool, is_first_attempt: bool
):
    """Update progress if this is the first attempt.

    Updates the progress tracking data for a word, but only if this is the first attempt
    at answering it in the current session.

    Args:
        update_fn: Function to call to update progress
        word_id: The word ID (e.g., 'word_000001')
        success: Whether the attempt was successful
        is_first_attempt: Whether this is the first attempt
    """
    if is_first_attempt:
        update_fn(word_id, success)
