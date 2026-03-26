from fastapi import FastAPI
from emails_api import get_emails
from pipeline import run_pipeline
from history_store import clear_history, get_history

app = FastAPI()

@app.post("/analyze")
def analyze(data: dict):
    return run_pipeline(data)


@app.get("/history")
def history():
    return get_history()


@app.delete("/history")
def delete_history():
    clear_history()
    return {"status": "cleared"}


@app.get("/emails")
def emails():
    return get_emails()
