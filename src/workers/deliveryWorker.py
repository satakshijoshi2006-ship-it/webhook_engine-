# src/workers/deliveryWorker.py
# THE HEART OF THE PROJECT
# Continuously polls DB for pending events and delivers them

import threading
import time
import os
from src.models import eventModel
from src.services.deliveryService import send_webhook
from src.services.retryService import get_next_retry_at, has_retries_remaining
from src.utils.constants import OUTCOME
from src.utils.logger import log_info, log_warn, log_error


WORKER_INTERVAL = int(os.getenv("WORKER_INTERVAL_SECONDS", 5))  # poll every 5 seconds


def process_event(event: dict):
    """
    Full delivery lifecycle for one event:
    1. Mark as processing (prevents duplicate handling)
    2. Send webhook
    3. On success → delivered
    4. On failure → schedule retry or mark dead
    5. Log the attempt
    """
    event_id = event["id"]
    retry_count = event["retry_count"]

    # STEP 1: Lock the event — prevent duplicate processing
    eventModel.set_status_processing(event_id)

    # STEP 2: Send the webhook
    result = send_webhook(event)

    # STEP 3: Log the attempt (always, success or failure)
    outcome = OUTCOME.SUCCESS if result["success"] else OUTCOME.FAILED
    eventModel.log_attempt(
        event_id=event_id,
        http_status=result["http_status"],
        outcome=outcome,
        error_message=result["error_message"],
        delivery_time_ms=result["delivery_time_ms"]
    )

    # STEP 4: Update event status based on result
    if result["success"]:
        eventModel.set_status_delivered(event_id)
        log_info(f"[WORKER] ✅ Delivered | event_id={event_id}")

    else:
        new_retry_count = retry_count + 1

        if has_retries_remaining(retry_count):
            # Schedule the next retry
            next_retry_at = get_next_retry_at(retry_count)
            eventModel.set_status_pending_retry(event_id, new_retry_count, next_retry_at)
            log_warn(
                f"[WORKER] 🔄 Retry scheduled | event_id={event_id} "
                f"retry={new_retry_count} next_at={next_retry_at}"
            )
        else:
            # All retries exhausted → dead
            eventModel.set_status_dead(event_id)
            log_error(f"[WORKER] 💀 Dead | event_id={event_id} after {new_retry_count} attempts")


def run_worker():
    """
    Worker loop — equivalent to setInterval in Node.js.
    Polls every WORKER_INTERVAL seconds for retryable events.
    """
    log_info(f"[WORKER] Started — polling every {WORKER_INTERVAL}s")

    while True:
        try:
            events = eventModel.get_retryable_events()

            if events:
                log_info(f"[WORKER] Found {len(events)} event(s) to process")
                for event in events:
                    try:
                        process_event(event)
                    except Exception as e:
                        # If processing crashes mid-way, reset back to pending so it retries
                        log_error(f"[WORKER] ⚠️ Crash processing event_id={event['id']}: {e}")
                        eventModel.set_status_pending_retry(
                            event["id"],
                            event["retry_count"],
                            event["next_retry_at"]
                        )

        except Exception as e:
            log_error(f"[WORKER] ⚠️ Worker loop error: {e}")

        # Sleep for WORKER_INTERVAL seconds, then poll again
        time.sleep(WORKER_INTERVAL)


def start_worker():
    """Start the background worker in a daemon thread."""
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    log_info("[WORKER] Background thread started")
    return worker_thread
