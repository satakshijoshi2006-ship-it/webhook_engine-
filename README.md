# Webhook Delivery Engine

A reliable, production-style webhook delivery system with automatic retry logic, HMAC signing, persistent storage, and a background worker.

---

## Architecture

```
Client
  ↓
Flask API (Express equivalent)
  ↓
SQLite Database
  ↓
Background Worker (polls every 5 seconds)
  ↓
Webhook Delivery (with HMAC signature)
```

---

## Tech Stack

| Purpose          | Technology               |
|------------------|--------------------------|
| Backend          | Python + Flask           |
| Database         | SQLite (built-in)        |
| HTTP Requests    | requests library         |
| Background Worker| threading (setInterval equivalent) |
| HMAC Signature   | hmac + hashlib (built-in)|
| Config           | python-dotenv            |

---

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Edit `.env` (already provided):
```
PORT=3000
SECRET_KEY=mysecretkey_webhook_engine_2026
WORKER_INTERVAL_SECONDS=5
```

### 3. Start the server

```bash
python run.py
```

Server starts on `http://localhost:3000`
Background worker starts automatically.

---

## API Endpoints

### Health Check
```
GET /health
```
Response:
```json
{ "status": "ok", "service": "webhook-engine" }
```

---

### Create Event
```
POST /events
Content-Type: application/json
```
Body:
```json
{
  "type": "payment.failed",
  "payload": {
    "user": "john",
    "amount": 200
  },
  "webhook_url": "https://your-server.com/webhook"
}
```
Response (201):
```json
{
  "message": "Event created successfully",
  "event": {
    "id": "uuid-here",
    "type": "payment.failed",
    "status": "pending",
    "retry_count": 0,
    "created_at": "2026-05-17T10:00:00"
  }
}
```

---

### Get All Events
```
GET /events
GET /events?status=dead
GET /events?status=pending
GET /events?status=delivered
GET /events?status=processing
```
Response (200):
```json
{
  "count": 3,
  "events": [ ... ]
}
```

---

### Get Single Event (with attempt history)
```
GET /events/:id
```
Response (200):
```json
{
  "id": "uuid",
  "type": "payment.failed",
  "status": "dead",
  "retry_count": 3,
  "attempts": [
    {
      "attempted_at": "2026-05-17T10:00:00",
      "http_status": 500,
      "outcome": "failed",
      "error_message": "HTTP 500",
      "delivery_time_ms": 120
    },
    {
      "attempted_at": "2026-05-17T10:00:30",
      "http_status": null,
      "outcome": "failed",
      "error_message": "Request timeout after 5s",
      "delivery_time_ms": 5003
    }
  ]
}
```

---

### Retry a Dead Event (Manual)
```
POST /events/:id/retry
```
Only works when `status == "dead"`.

Response (200):
```json
{
  "message": "Event re-queued for delivery",
  "event": { "status": "pending", "retry_count": 0, ... }
}
```

---

## Status Flow

```
Event Created
    ↓
  pending
    ↓
Worker picks it up
    ↓
 processing        ← (prevents duplicate handling on crash)
    ↓
Webhook sent
    ↙           ↘
 SUCCESS         FAILURE
    ↓               ↓
 delivered      retry_count++
                    ↓
            has retries left?
              ↙          ↘
            YES            NO
              ↓              ↓
           pending          dead
        (scheduled)
```

---

## Retry Logic

| Attempt       | When                        |
|---------------|-----------------------------|
| Initial try   | Immediately on event creation |
| Retry 1       | 30 seconds after failure    |
| Retry 2       | 5 minutes after failure     |
| Retry 3       | 30 minutes after failure    |
| After retry 3 | Status = **dead**           |

**Total attempts: 4** (1 initial + 3 retries)

The worker polls the DB every 5 seconds for events where:
- `status = 'pending'`
- `next_retry_at <= now`

---

## HMAC Signature Verification

Every outgoing webhook includes an `X-Webhook-Signature` header.

**How it's generated (server side):**
```python
import hmac, hashlib, json

signature = hmac.new(
    SECRET_KEY.encode("utf-8"),
    json.dumps(payload, separators=(",", ":")).encode("utf-8"),
    hashlib.sha256
).hexdigest()

# Sent as header:
# X-Webhook-Signature: abc123def456...
```

**How the receiver verifies it:**
```python
import hmac, hashlib, json

def verify_webhook(request_body_bytes, received_signature, secret_key):
    expected = hmac.new(
        secret_key.encode("utf-8"),
        request_body_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature)
```

If the signatures match → the webhook is authentic and untampered.

---

## Persistence After Restart

Because all data is stored in **SQLite** (`database/webhook.db`):

- All events survive server restarts
- Retry schedules persist — `next_retry_at` is stored in DB
- Worker re-reads from DB on startup — **retries continue automatically**

This is a key advantage over in-memory queues.

---

## Worker Locking (Duplicate Prevention)

When the worker picks an event, it immediately sets `status = 'processing'`.

This means:
- If the server crashes mid-delivery, the event won't be re-processed by another loop cycle
- The event stays in `processing` until success/failure is confirmed
- On crash recovery, a separate cleanup step can reset stuck `processing` events

---

## Project Structure

```
webhook-engine/
│
├── run.py                     ← Entry point: python run.py
├── .env                       ← Environment variables
├── requirements.txt
├── .gitignore
│
├── database/
│   └── webhook.db             ← SQLite file (auto-created)
│
└── src/
    ├── config/
    │   └── db.py              ← DB connection + table creation
    │
    ├── routes/
    │   └── eventRoutes.py     ← API route registration
    │
    ├── controllers/
    │   └── eventController.py ← Request/response handling
    │
    ├── services/
    │   ├── eventService.py    ← Business logic
    │   ├── deliveryService.py ← HTTP webhook sending (most important)
    │   ├── retryService.py    ← Retry interval calculation
    │   └── signatureService.py← HMAC signature generation
    │
    ├── workers/
    │   └── deliveryWorker.py  ← Background polling worker (heart of system)
    │
    ├── models/
    │   └── eventModel.py      ← All DB queries
    │
    └── utils/
        ├── constants.py       ← Status constants, retry intervals
        └── logger.py          ← Structured logging
```

---

## Database Schema

**events table:**
```sql
CREATE TABLE events (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    payload       TEXT NOT NULL,        -- JSON string
    webhook_url   TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending',
    retry_count   INTEGER NOT NULL DEFAULT 0,
    next_retry_at DATETIME,
    created_at    DATETIME NOT NULL
);
```

**attempts table:**
```sql
CREATE TABLE attempts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id         TEXT NOT NULL,
    attempted_at     DATETIME NOT NULL,
    http_status      INTEGER,           -- null on timeout/connection error
    outcome          TEXT NOT NULL,     -- 'success' | 'failed'
    error_message    TEXT,
    delivery_time_ms INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
```

---

## Testing Scenarios

### Test 1: Successful delivery
```bash
curl -X POST http://localhost:3000/events \
  -H "Content-Type: application/json" \
  -d '{"type":"payment.success","payload":{"amount":500},"webhook_url":"https://httpbin.org/post"}'
```
Expected: event goes `pending → processing → delivered`

### Test 2: Failed delivery with retries
Use an invalid URL like `https://invalid.nonexistent.example/hook`
Expected: 4 attempts total, then `status = dead`

### Test 3: Check attempt history
```bash
curl http://localhost:3000/events/{event_id}
```

### Test 4: Manual retry
```bash
curl -X POST http://localhost:3000/events/{event_id}/retry
```

### Test 5: Restart persistence
Stop server → restart → retries continue from where they left off ✅

---

## What Was NOT Built (by design)

- ❌ Frontend / React UI
- ❌ Authentication / login
- ❌ Redis / RabbitMQ / BullMQ / Kafka
- ❌ Docker / Kubernetes
- ❌ Microservices

This is intentional. The assessment tests backend fundamentals, async processing, retry systems, API design, and clean architecture — not infrastructure complexity.
