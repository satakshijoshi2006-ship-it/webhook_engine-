

import uuid
from datetime import datetime
from src.models import eventModel
from src.utils.logger import log_info


def create_event(event_type: str, payload: dict, webhook_url: str) -> dict:
    """
    Create a new webhook event:
    - Generate UUID
    - Store in DB with status=pending
    - next_retry_at = now (so worker picks it up immediately)
    """
    event_id = str(uuid.uuid4())
    eventModel.create_event(event_id, event_type, payload, webhook_url)
    log_info(f"[EVENT] Created event_id={event_id} type={event_type}")
    return eventModel.get_event_by_id(event_id)


def get_all_events(status_filter=None) -> list:
    """Return all events, optionally filtered by status."""
    return eventModel.get_all_events(status_filter)


def get_event_with_attempts(event_id: str) -> dict | None:
    """Return event + full attempt history."""
    event = eventModel.get_event_by_id(event_id)
    if not event:
        return None
    attempts = eventModel.get_attempts_by_event_id(event_id)
    event["attempts"] = attempts
    return event


def retry_dead_event(event_id: str) -> bool:
    """
    Manually retry a dead event.
    Resets retry_count=0 and status=pending.
    Returns True if event was reset, False otherwise.
    """
    success = eventModel.reset_event_for_retry(event_id)
    if success:
        log_info(f"[EVENT] Manual retry triggered for event_id={event_id}")
    return success
