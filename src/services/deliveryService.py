

import json
import time
import requests
from src.services.signatureService import generate_signature
from src.utils.logger import log_info, log_error


TIMEOUT_SECONDS = 5 


def send_webhook(event: dict) -> dict:
    """
    Send a POST request to the event's webhook_url.
    
    Returns a dict:
    {
        "success": bool,
        "http_status": int or None,
        "error_message": str or None,
        "delivery_time_ms": int
    }
    """
    payload_raw = event["payload"]
    
    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw)
        except (json.JSONDecodeError, TypeError):
            payload = payload_raw
    else:
        payload = payload_raw
    webhook_url = event["webhook_url"]
    event_id = event["id"]

   
    webhook_body = {
        "event_id": event_id,
        "type": event["type"],
        "payload": payload
    }

  
    signature = generate_signature(webhook_body)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Event-ID": event_id,
        "X-Event-Type": event["type"]
    }

    start_time = time.time()

    try:
        log_info(f"[DELIVERY] Sending webhook → {webhook_url} | event_id={event_id}")
        
        response = requests.post(
            webhook_url,
            json=webhook_body,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )

        delivery_time_ms = int((time.time() - start_time) * 1000)
        http_status = response.status_code
        success = 200 <= http_status < 300

        if success:
            log_info(f"[DELIVERY] ✅ Success | event_id={event_id} | status={http_status} | {delivery_time_ms}ms")
        else:
            log_error(f"[DELIVERY] ❌ Failed | event_id={event_id} | status={http_status} | {delivery_time_ms}ms")

        return {
            "success": success,
            "http_status": http_status,
            "error_message": None if success else f"HTTP {http_status}",
            "delivery_time_ms": delivery_time_ms
        }

    except requests.exceptions.Timeout:
        delivery_time_ms = int((time.time() - start_time) * 1000)
        log_error(f"[DELIVERY] ⏱ Timeout | event_id={event_id} | {delivery_time_ms}ms")
        return {
            "success": False,
            "http_status": None,
            "error_message": "Request timeout after 5s",
            "delivery_time_ms": delivery_time_ms
        }

    except requests.exceptions.ConnectionError as e:
        delivery_time_ms = int((time.time() - start_time) * 1000)
        log_error(f"[DELIVERY] 🔌 Connection error | event_id={event_id} | {str(e)}")
        return {
            "success": False,
            "http_status": None,
            "error_message": f"Connection error: {str(e)[:100]}",
            "delivery_time_ms": delivery_time_ms
        }

    except Exception as e:
        delivery_time_ms = int((time.time() - start_time) * 1000)
        log_error(f"[DELIVERY] 💥 Unexpected error | event_id={event_id} | {str(e)}")
        return {
            "success": False,
            "http_status": None,
            "error_message": f"Unexpected error: {str(e)[:100]}",
            "delivery_time_ms": delivery_time_ms
        }
