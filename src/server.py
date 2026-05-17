

import os
import sys


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from flask import Flask
from src.config.db import init_db
from src.routes.eventRoutes import event_bp
from src.workers.deliveryWorker import start_worker
from src.models.eventModel import recover_stuck_processing_events
from src.utils.logger import log_info


def create_app():
    app = Flask(__name__)

   
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


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 3000))

    
    init_db()

   
    recovered = recover_stuck_processing_events()
    if recovered:
        log_info(f"[STARTUP] Recovered {recovered} stuck 'processing' event(s) → reset to 'pending'")

   
    app = create_app()

    start_worker()

    log_info(f"🚀 Webhook Engine running on http://localhost:{PORT}")
    log_info("📋 Routes: POST /events | GET /events | GET /events/:id | POST /events/:id/retry | GET /health")

  
    app.run(host="0.0.0.0", port=PORT, debug=False)
