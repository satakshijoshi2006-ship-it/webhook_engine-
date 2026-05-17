

from flask import Blueprint
from src.controllers.eventController import (
    create_event,
    get_all_events,
    get_event,
    retry_event,
    health_check
)

event_bp = Blueprint("events", __name__)

event_bp.route("/health", methods=["GET"])(health_check)


event_bp.route("/events", methods=["POST"])(create_event)
event_bp.route("/events", methods=["GET"])(get_all_events)
event_bp.route("/events/<string:event_id>", methods=["GET"])(get_event)
event_bp.route("/events/<string:event_id>/retry", methods=["POST"])(retry_event)
