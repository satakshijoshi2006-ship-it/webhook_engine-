

from datetime import datetime, timedelta
from src.utils.constants import RETRY_INTERVALS, MAX_RETRIES


def get_next_retry_at(retry_count: int):
    """
    Returns the datetime for the next retry attempt.
    
    Retry schedule:
      retry_count 0 → wait 30 seconds
      retry_count 1 → wait 5 minutes (300s)
      retry_count 2 → wait 30 minutes (1800s)
    
    Returns None if retries are exhausted.
    """
    if retry_count >= MAX_RETRIES:
        return None  # no more retries

    wait_seconds = RETRY_INTERVALS[retry_count]
    next_retry = datetime.utcnow() + timedelta(seconds=wait_seconds)
    return next_retry.isoformat()


def has_retries_remaining(retry_count: int) -> bool:
    """Check if the event can still be retried."""
    return retry_count < MAX_RETRIES
