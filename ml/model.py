# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from __future__ import annotations

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import MaxAbsScaler

from sqli_features import HandcraftedFeatures, normalize

# NOTE: joblib pickles `HandcraftedFeatures` by its module path, so
# `sqli_features` must be importable as a *top-level* module wherever the
# saved model is loaded (see proxy/main.py, which puts ml/ on sys.path).


def build_pipeline(classifier: str = "logreg", random_state: int = 0) -> Pipeline:
    """Construct the full feature + classifier pipeline.

    Two feature branches run in parallel and are concatenated:
      * char n-gram TF-IDF over the URL-decoded, lowercased text
      * handcrafted numeric features over the raw text

    `classifier` is either "logreg" (fast, calibrated probabilities) or
    "rf" (random forest, exposes feature importances).
    """
    tfidf = TfidfVectorizer(
        analyzer="char",
        ngram_range=(1, 5),
        min_df=2,
        max_features=30000,
        preprocessor=normalize,
        lowercase=False,
    )

    features = FeatureUnion([
        ("char_tfidf", tfidf),
        ("handcrafted", Pipeline([
            ("raw", HandcraftedFeatures()),
            ("scale", MaxAbsScaler()),
        ])),
    ])

    if classifier == "logreg":
        clf = LogisticRegression(
            max_iter=2000,
            C=4.0,
            class_weight="balanced",
        )
    elif classifier == "rf":
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        )
    else:
        raise ValueError(f"unknown classifier {classifier!r}; use 'logreg' or 'rf'")

    return Pipeline([("features", features), ("clf", clf)])


class SqliDetector:
    """Runtime wrapper around a trained pipeline. Load once at start-up."""

    def __init__(self, model_path: str = "sqli_model.joblib", threshold: float = 0.5):
        self.pipeline: Pipeline = joblib.load(model_path)
        self.threshold = threshold

    def _proba(self, texts):
        clf = self.pipeline
        if hasattr(clf, "predict_proba"):
            return clf.predict_proba(texts)[:, 1]
        # fallback for classifiers without predict_proba
        scores = clf.decision_function(texts)
        return 1.0 / (1.0 + np.exp(-scores))

    def predict(self, text: str) -> dict:
        p = float(self._proba([text])[0])
        is_attack = p >= self.threshold
        return {
            "is_attack": bool(is_attack),
            "label": "malicious" if is_attack else "benign",
            "confidence": p if is_attack else 1.0 - p,
            "attack_probability": p,
        }

    def predict_batch(self, texts):
        probs = self._proba(list(texts))
        out = []
        for p in probs:
            p = float(p)
            is_attack = p >= self.threshold
            out.append({
                "is_attack": bool(is_attack),
                "label": "malicious" if is_attack else "benign",
                "confidence": p if is_attack else 1.0 - p,
                "attack_probability": p,
            })
        return out
