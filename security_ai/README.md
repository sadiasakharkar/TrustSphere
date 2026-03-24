# Security AI

Offline multi-modal AI security platform scaffold for TrustSphere.

Implemented in this module:
- Phishing email detector pipeline
- Feature engineering
- Train/val/test split
- Hyperparameter search
- Evaluation
- Explainability export hooks
- Model export
- Inference script
- FastAPI-ready app

Run training:

```bash
PYTHONPATH=. trustsphere-ai/.venv/bin/python security_ai/training/train_phishing_email.py
```

Run inference:

```bash
PYTHONPATH=. trustsphere-ai/.venv/bin/python security_ai/predict_email.py \
  --subject "urgent payment required" \
  --body "verify account immediately" \
  --sender "security@bank-alerts.example"
```
