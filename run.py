

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from src.config.db import init_db
from src.routes.eventRoutes import event_bp
from src.workers.deliveryWorker import start_worker
from src.models.eventModel import recover_stuck_processing_events
from src.utils.logger import log_info


def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def home():
     return "Application Running Successfully"
    @app.route("/health", methods=["GET"])
    def health():
      return {
        "status": "healthy",
        "service": "webhook-engine"
    }, 200

    
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def handle_options(path):
        from flask import Response
        return Response(status=200)

    app.register_blueprint(event_bp)
    return app


PORT = int(os.getenv("PORT", 3000))

init_db()


recovered = recover_stuck_processing_events()
if recovered:
    log_info(f"[STARTUP] Recovered {recovered} stuck 'processing' event(s) → reset to 'pending'")


app = create_app()


start_worker()

log_info(f"🚀 Webhook Engine running on http://localhost:{PORT}")
log_info("📋 Endpoints:")
log_info("   POST /events              — Create event")
log_info("   GET  /events              — List all events (?status=dead|pending|delivered)")
log_info("   GET  /events/:id          — Get event + attempt history")
log_info("   POST /events/:id/retry    — Retry a dead event")
log_info("   GET  /health              — Health check")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
