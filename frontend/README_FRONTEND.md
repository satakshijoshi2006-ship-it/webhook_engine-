# Webhook Engine — Frontend Dashboard

## How to Use

### Step 1 — Start the backend
```bash
cd Shatakshi_Nestack_Submission
pip install -r requirements.txt
python run.py
```
Server runs at `http://localhost:3000`

### Step 2 — Open the frontend
Simply open the file in your browser:
```
frontend/index.html
```
Double-click it, or drag it into Chrome/Edge/Firefox.

> No build step. No npm. Just open the HTML file directly.

---

## Features

| Feature | Description |
|---|---|
| **Live Stats** | Total / Delivered / Pending / Dead counts, auto-updates every 5s |
| **Event Log** | Table with all events, filterable by status |
| **Quick Fire** | Fire a test webhook directly from the dashboard |
| **Create Event** | Full form to create events with custom type/payload/URL |
| **Event Detail Drawer** | Click any row to see full event info + attempt history |
| **Retry Dead Events** | One-click retry button inside the drawer for dead events |
| **Health Indicator** | Live API connection status in the sidebar |
| **Auto-Refresh** | Dashboard refreshes every 5 seconds automatically |

## API Base URL

The dashboard defaults to `http://localhost:3000`.
If your backend runs on a different port, update the **API** field in the top-right of the dashboard.

## Test URLs

| URL | Result |
|---|---|
| `https://httpbin.org/post` | Always succeeds (200) |
| `https://invalid.nonexistent.bad/hook` | Always fails → triggers retry chain |
