# TrustSphere Browser Extension Demo

This folder contains a minimal Chrome extension for the hackathon demo.

## What it does

- reads visible page text
- sends the first 1000 characters to `http://127.0.0.1:8000/analyze`
- shows a floating popup when TrustSphere returns `HIGH` or `MEDIUM`
- displays both severity and explainable fraud reasons

## Load it in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select this folder:

```text
TrustSphere/browser-extension
```

## Demo backend

Run the lightweight backend from `backend/ml_service` so the extension can call:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Start it from this directory:

```text
TrustSphere/backend/ml_service
```
