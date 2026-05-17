# Webhook Delivery Engine

A reliable production-style webhook delivery system with automatic retry logic, HMAC signing, persistent storage, a background worker, and a live monitoring dashboard.

---

# Live Deployment

## Frontend Dashboard

https://shatakshi-nestack-submission.vercel.app/

## Backend API

https://shatakshi-nestack-submission.onrender.com/

---

# Architecture

Client
↓
Frontend Dashboard (HTML/CSS/JS)
↓
Flask API Backend
↓
SQLite Database
↓
Background Worker (polls every 5 seconds)
↓
Webhook Delivery with HMAC Signature

---

# Tech Stack

| Purpose           | Technology            |
| ----------------- | --------------------- |
| Frontend          | HTML, CSS, JavaScript |
| Backend           | Python + Flask        |
| Database          | SQLite                |
| HTTP Requests     | requests              |
| Background Worker | threading             |
| HMAC Signature    | hmac + hashlib        |
| Deployment        | Vercel + Render       |
| Config            | python-dotenv         |

---

# Features

* Webhook event creation
* Automatic retry mechanism
* Dead event recovery
* Event delivery tracking
* Delivery attempt history
* HMAC webhook signature verification
* Persistent SQLite storage
* Background polling worker
* Real-time dashboard refresh
* Health monitoring endpoint
* Status-based event filtering

---

# Setup & Run

## 1. Clone Repository

```bash
git clone <repository-url>
cd Shatakshi_Nestack_Submission
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment

Edit `.env`

```env
PORT=3000
SECRET_KEY=mysecretkey_webhook_engine_2026
WORKER_INTERVAL_SECONDS=5
```

---

## 4. Run Backend

```bash
python run.py
```

Backend runs on:

```text
http://localhost:3000
```

---

## 5. Run Frontend

Open `index.html` in browser.

---

# API Endpoints

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "webhook-engine"
}
```

---

## Create Event

```http
POST /events
```

Request Body:

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

---

## Get All Events

```http
GET /events
GET /events?status=dead
GET /events?status=pending
GET /events?status=delivered
GET /events?status=processing
```

---

## Get Single Event

```http
GET /events/:id
```

---

## Retry Dead Event

```http
POST /events/:id/retry
```

---

# Status Flow

```text
Event Created
    ↓
 pending
    ↓
Worker picks it up
    ↓
processing
    ↓
Webhook sent
   ↙        ↘
SUCCESS    FAILURE
   ↓           ↓
delivered   retry_count++
                ↓
       retries left?
          ↙      ↘
        YES       NO
         ↓         ↓
      pending     dead
```

---

# Retry Logic

| Attempt     | Timing     |
| ----------- | ---------- |
| Initial Try | Immediate  |
| Retry 1     | 30 seconds |
| Retry 2     | 5 minutes  |
| Retry 3     | 30 minutes |
| Final State | dead       |

Total Attempts = 4

---

# HMAC Signature

Every outgoing webhook includes:

```text
X-Webhook-Signature
```

Generated using SHA256 HMAC signing.

---

# Persistence

All events are stored in SQLite database:

```text
database/webhook.db
```

This ensures:

* Events survive server restarts
* Retry schedules persist
* Worker resumes automatically after restart

---

# Project Structure

```text
webhook-engine/
│
├── run.py
├── requirements.txt
├── .env
├── database/
│   └── webhook.db
│
└── src/
    ├── config/
    ├── controllers/
    ├── models/
    ├── routes/
    ├── services/
    ├── utils/
    └── workers/
```

---

# Testing Scenarios

## Successful Delivery

```bash
curl -X POST http://localhost:3000/events \
-H "Content-Type: application/json" \
-d '{"type":"payment.success","payload":{"amount":500},"webhook_url":"https://httpbin.org/post"}'
```

---

## Failed Delivery with Retries

Use invalid webhook URL.

Expected:

* automatic retries
* final status becomes `dead`

---

## Restart Persistence Test

Stop server → restart server → retries continue automatically.

---

# Deployment

## Frontend

Deployed on Vercel

## Backend

Deployed on Render

---

# Contributors Added for Evaluation

* [bishal@nestack.com](mailto:bishal@nestack.com)
* [sannidhya@nestack.com](mailto:sannidhya@nestack.com)
* [sanjay@nestack.com](mailto:sanjay@nestack.com)

---

# Author

Shatakshi
