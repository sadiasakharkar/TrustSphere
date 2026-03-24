# TrustSphere AI

Offline AI pipeline scaffold for TrustSphere.

## Structure

- `data/`: raw and processed datasets
- `notebooks/`: experimentation notebooks
- `src/`: core ingestion, features, models, graph, llm, pipeline, utils
- `saved_models/`: serialized model artifacts
- `api/`: FastAPI app

## Quick Start

```bash
cd trustsphere-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload
```

## Notes

- This is scaffolded for future TrustSphere backend/ML integration.
- The Python modules currently contain lightweight placeholder implementations.
