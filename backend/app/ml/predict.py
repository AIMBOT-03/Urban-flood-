import os
import joblib
import pandas as pd
from .train_model import FEATURES, MODEL_PATH, risk_score, score_to_label

_cache = {"model": None}


def _load_model():
    if _cache["model"] is None and os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        _cache["model"] = bundle["model"]
    return _cache["model"]


def predict_risk(features: dict) -> dict:
    """
    features: dict with the 9 raw feature keys (see FEATURES).
    Returns {"level": "Low"|"Medium"|"High", "probability": float 0-1, "source": "ml"|"rule_fallback"}
    """
    model = _load_model()
    vector = pd.DataFrame([[features[f] for f in FEATURES]], columns=FEATURES)

    if model is not None:
        probs = model.predict_proba(vector)[0]
        classes = list(model.classes_)
        level = classes[int(probs.argmax())]
        high_idx = classes.index("High") if "High" in classes else None
        confidence = float(probs.max())
        return {
            "level": level,
            "probability": confidence,
            "high_probability": float(probs[high_idx]) if high_idx is not None else None,
            "source": "ml",
        }

    # Cold-start / model-unavailable fallback: rule-based scoring
    score = risk_score(features)
    return {
        "level": score_to_label(score),
        "probability": round(score, 3),
        "high_probability": score,
        "source": "rule_fallback",
    }
