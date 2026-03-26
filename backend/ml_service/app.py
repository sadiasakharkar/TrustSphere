from fastapi import FastAPI
from pipeline import run_pipeline

app = FastAPI()

@app.post("/analyze")
def analyze(data: dict):
    return run_pipeline(data)