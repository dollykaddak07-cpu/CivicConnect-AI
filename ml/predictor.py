"""CivicConnect ML inference helper.

Model: TF-IDF vectorization + Logistic Regression classifier.
The model is trained on the included curated civic complaint dataset.
"""
from pathlib import Path
import json
import joblib

BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "complaint_classifier.joblib"
METRICS_PATH = BASE / "metrics.json"

_model = None
_metrics = {}


def load_model():
    global _model, _metrics
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    if not _metrics and METRICS_PATH.exists():
        _metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return _model


def predict(text: str):
    model = load_model()
    if not model or not text.strip():
        return None
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)
    best_index = int(probabilities.argmax())
    return {
        "category": classes[best_index],
        "confidence": round(float(probabilities[best_index]) * 100, 2),
        "probabilities": {
            cls: round(float(probabilities[i]) * 100, 2)
            for i, cls in enumerate(classes)
        },
        "model": "Word + Character TF-IDF + Logistic Regression"
    }


def info():
    load_model()
    return {
        "model": _metrics.get("model", "Word + Character TF-IDF + Logistic Regression"),
        "task": _metrics.get("task", "Civic complaint category classification"),
        "dataset": _metrics.get("dataset", "complaint_dataset.csv"),
        "dataset_rows": _metrics.get("dataset_rows", 0),
        "train_rows": _metrics.get("train_rows", 0),
        "test_rows": _metrics.get("test_rows", 0),
        "test_accuracy": round(float(_metrics.get("test_accuracy", 0)) * 100, 2),
        "weighted_f1": round(float(_metrics.get("weighted_f1", 0)) * 100, 2),
        "classes": _metrics.get("classes", []),
        "ready": _model is not None,
    }
