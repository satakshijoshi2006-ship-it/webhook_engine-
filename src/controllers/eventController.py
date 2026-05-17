

from flask import request, jsonify
from src.services import eventService
from src.utils.logger import log_info, log_error


def create_event():
    """
    POST /events
    Body: { "type": "...", "payload": {...}, "webhook_url": "..." }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    event_type = data.get("type")
    payload = data.get("payload")
    webhook_url = data.get("webhook_url")

    if not event_type:
        return jsonify({"error": "'type' is required"}), 400
    if payload is None:
        return jsonify({"error": "'payload' is required"}), 400
    if not webhook_url:
        return jsonify({"error": "'webhook_url' is required"}), 400
    if not webhook_url.startswith(("http://", "https://")):
        return jsonify({"error": "'webhook_url' must be a valid URL"}), 400

    try:
        event = eventService.create_event(event_type, payload, webhook_url)
        return jsonify({
            "message": "Event created successfully",
            "event": event
        }), 201
    except Exception as e:
        log_error(f"[CONTROLLER] Error creating event: {e}")
        return jsonify({"error": "Internal server error"}), 500


def get_all_events():
    """
    GET /events
    Optional query param: ?status=dead|pending|delivered|processing
    """
    status_filter = request.args.get("status")
    try:
        events = eventService.get_all_events(status_filter)
        return jsonify({
            "count": len(events),
            "events": events
        }), 200
    except Exception as e:
        log_error(f"[CONTROLLER] Error fetching events: {e}")
        return jsonify({"error": "Internal server error"}), 500


def get_event(event_id):
    """
    GET /events/:id
    Returns event details + full attempt history
    """
    try:
        event = eventService.get_event_with_attempts(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404
        return jsonify(event), 200
    except Exception as e:
        log_error(f"[CONTROLLER] Error fetching event {event_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


def retry_event(event_id):
    """
    POST /events/:id/retry
    Only works for dead events — resets and re-queues
    """
    try:
        from src.models import eventModel
        event = eventModel.get_event_by_id(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404
        if event["status"] != "dead":
            return jsonify({
                "error": f"Only dead events can be retried. Current status: '{event['status']}'"
            }), 400

        success = eventService.retry_dead_event(event_id)
        if success:
            updated = eventModel.get_event_by_id(event_id)
            return jsonify({
                "message": "Event re-queued for delivery",
                "event": updated
            }), 200
        else:
            return jsonify({"error": "Failed to retry event"}), 500

    except Exception as e:
        log_error(f"[CONTROLLER] Error retrying event {event_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


def health_check():
    """GET /health — server liveness check"""
    return jsonify({"status": "ok", "service": "webhook-engine"}), 200
