"""
Generates a synthetic training dataset for the flood-risk Random Forest model
and trains/saves it. Run directly: `python -m app.ml.train_model`

There is no real historical flood dataset for these wards yet (see project
future-scope: real IMD/CWC/CGWB integration). Labels here are produced by a
weighted rule-of-thumb flood-risk formula plus noise, so the RF learns a
smoothed, non-linear approximation of that formula instead of exact thresholds.
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

FEATURES = [
    "rainfall_mm_hr",
    "river_level_m",
    "river_rise_rate_m_hr",
    "elevation_m",
    "slope_deg",
    "distance_to_river_km",
    "drainage_density",
    "active_drain_count",
    "citizen_report_count",
]

# min/max used for normalizing each feature when computing the synthetic
# label score, and reused by the rule-based fallback at inference time.
#
# elevation_m: (1, 200) reflects the real spread across the 6 cities, not a
# guess -- Puri/Kendrapara sit near sea level (~2-9m) while Sambalpur, on the
# western plateau near Hirakud Dam, sits at ~130-196m (city figure commonly
# cited as ~186m). Earlier zones.json had Sambalpur at 15-27m, which
# understated by nearly 10x how much its elevation should suppress flood
# risk relative to the coastal cities -- fixed 2026-08-27.
#
# rainfall_mm_hr / river_level_m: no verified real CWC gauge danger-level or
# IMD hourly-intensity figures were available (see project memory), so these
# stay placeholder ranges sized against Odisha's known extreme-rainfall
# events (e.g. Cyclone Phailin/Fani) rather than a specific cited station
# threshold. Don't present these two as verified real numbers.
FEATURE_RANGES = {
    "rainfall_mm_hr": (0, 120),
    "river_level_m": (1, 12),
    "river_rise_rate_m_hr": (-0.5, 2.0),
    "elevation_m": (1, 200),
    "slope_deg": (0, 15),
    "distance_to_river_km": (0.05, 8),
    "drainage_density": (0.3, 6),
    "active_drain_count": (0, 20),
    "citizen_report_count": (0, 15),
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")


def _norm(value, key):
    lo, hi = FEATURE_RANGES[key]
    return np.clip((value - lo) / (hi - lo), 0, 1)


def risk_score(row: dict) -> float:
    """Weighted 0-1 flood risk score used both to generate synthetic labels
    and as the rule-based cold-start fallback when the ML model can't be used."""
    score = (
        0.28 * _norm(row["rainfall_mm_hr"], "rainfall_mm_hr")
        + 0.20 * _norm(row["river_level_m"], "river_level_m")
        + 0.15 * _norm(row["river_rise_rate_m_hr"], "river_rise_rate_m_hr")
        - 0.10 * _norm(row["elevation_m"], "elevation_m")
        - 0.05 * _norm(row["slope_deg"], "slope_deg")
        - 0.08 * _norm(row["distance_to_river_km"], "distance_to_river_km")
        - 0.09 * _norm(row["drainage_density"], "drainage_density")
        + 0.08 * _norm(row["active_drain_count"], "active_drain_count")
        + 0.07 * _norm(row["citizen_report_count"], "citizen_report_count")
    )
    # shift/scale so the weighted sum (which can go slightly negative
    # because of the subtracted terms) maps onto a clean 0-1 band, tuned so
    # calm-weather baselines read Low/borderline-Medium and only genuine
    # heavy-rain + rising-river conditions push a zone into High
    return float(np.clip(score + 0.20, 0, 1))


def score_to_label(score: float) -> str:
    if score < 0.35:
        return "Low"
    if score < 0.62:
        return "Medium"
    return "High"


def generate_dataset(n_samples: int = 6000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {key: rng.uniform(lo, hi, n_samples) for key, (lo, hi) in FEATURE_RANGES.items()}
    df = pd.DataFrame(data)

    scores = df.apply(lambda r: risk_score(r.to_dict()), axis=1)
    noise = rng.normal(0, 0.06, n_samples)
    noisy_scores = np.clip(scores + noise, 0, 1)
    df["label"] = [score_to_label(s) for s in noisy_scores]
    return df


def train_and_save(n_samples: int = 6000):
    df = generate_dataset(n_samples)
    X = df[FEATURES]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    print("Validation report:")
    print(classification_report(y_test, clf.predict(X_test)))

    joblib.dump({"model": clf, "features": FEATURES}, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")
    return clf


if __name__ == "__main__":
    train_and_save()
