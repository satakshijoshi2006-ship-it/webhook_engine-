

import json
from datetime import datetime
from src.config.db import get_connection


def _deserialize_event(row: dict) -> dict:
    """Parse the payload JSON string back to a dict for API responses."""
    if row and isinstance(row.get("payload"), str):
        try:
            row["payload"] = json.loads(row["payload"])
        except (json.JSONDecodeError, TypeError):
            pass  
    return row


def create_event(event_id, event_type, payload, webhook_url):
    """Insert a new event into the DB with status=pending."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO events (id, type, payload, webhook_url, status, retry_count, next_retry_at, created_at)
        VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)
        """,
        (event_id, event_type, json.dumps(payload), webhook_url, now, now)
    )
    conn.commit()
    conn.close()


def get_all_events(status_filter=None):
    """Fetch all events, optionally filtered by status."""
    conn = get_connection()
    if status_filter:
        rows = conn.execute(
            "SELECT * FROM events WHERE status = ? ORDER BY created_at DESC",
            (status_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [_deserialize_event(dict(row)) for row in rows]


def get_event_by_id(event_id):
    """Fetch a single event by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()
    conn.close()
    return _deserialize_event(dict(row)) if row else None


def get_attempts_by_event_id(event_id):
    """Fetch all delivery attempts for an event."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM attempts WHERE event_id = ? ORDER BY attempted_at ASC",
        (event_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def recover_stuck_processing_events():
    """
    On server startup, reset any events stuck in 'processing' back to 'pending'.
    This handles the case where the server crashed mid-delivery.
    """
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """
        UPDATE events
        SET status = 'pending', next_retry_at = ?
        WHERE status = 'processing'
        """,
        (now,)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected


def get_retryable_events():
    """
    Fetch events that the worker should process:
    status = pending AND next_retry_at <= now
    """
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    rows = conn.execute(
        """
        SELECT * FROM events
        WHERE status = 'pending'
        AND next_retry_at <= ?
        """,
        (now,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def set_status_processing(event_id):
    """Mark event as processing to prevent duplicate handling."""
    conn = get_connection()
    conn.execute(
        "UPDATE events SET status = 'processing' WHERE id = ?",
        (event_id,)
    )
    conn.commit()
    conn.close()


def set_status_delivered(event_id):
    """Mark event as successfully delivered."""
    conn = get_connection()
    conn.execute(
        "UPDATE events SET status = 'delivered' WHERE id = ?",
        (event_id,)
    )
    conn.commit()
    conn.close()


def set_status_pending_retry(event_id, retry_count, next_retry_at):
    """Schedule a retry: bump retry_count and set next_retry_at."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE events
        SET status = 'pending', retry_count = ?, next_retry_at = ?
        WHERE id = ?
        """,
        (retry_count, next_retry_at, event_id)
    )
    conn.commit()
    conn.close()


def set_status_dead(event_id):
    """Mark event as dead (all retries exhausted)."""
    conn = get_connection()
    conn.execute(
        "UPDATE events SET status = 'dead' WHERE id = ?",
        (event_id,)
    )
    conn.commit()
    conn.close()


def reset_event_for_retry(event_id):
    """Reset a dead event so it can be retried manually."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """
        UPDATE events
        SET status = 'pending', retry_count = 0, next_retry_at = ?
        WHERE id = ? AND status = 'dead'
        """,
        (now, event_id)
    )
    conn.commit()
    affected = cursor.rowcount  # FIX: rowcount reflects only this statement; total_changes is cumulative
    conn.close()
    return affected > 0


def log_attempt(event_id, http_status, outcome, error_message, delivery_time_ms):
    """Insert a delivery attempt record."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO attempts (event_id, attempted_at, http_status, outcome, error_message, delivery_time_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_id, now, http_status, outcome, error_message, delivery_time_ms)
    )
    conn.commit()
    conn.close()
