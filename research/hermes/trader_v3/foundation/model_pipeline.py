"""Model pipeline skeleton (smoke test only). dataset -> train/val/test -> artifact -> registry.

Stage-1: build + validate the pipeline, NOT find the best model.
Baseline = logistic regression (numpy, deterministic).
"""
from __future__ import annotations
import hashlib
import json
import os
import numpy as np


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def build_dataset(features: dict, label_arr, feature_names=None):
    names = feature_names or [k for k, v in features.items()
                              if hasattr(v, "shape") and k not in
                              ("order_flow_imbalance_status", "micro_price_status")]
    X = np.stack([features[k] for k in names], axis=1).astype(np.float64)
    y = np.asarray(label_arr, dtype=np.float64)
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    return X[mask], y[mask], names, mask


def standardize(X, mu=None, sd=None):
    if mu is None:
        mu = np.nanmean(X, axis=0)
        sd = np.nanstd(X, axis=0)
        sd[sd == 0] = 1.0
    return (X - mu) / sd, mu, sd


def train_logistic(X, y_bin, lr=0.1, epochs=200, l2=1e-3):
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    for _ in range(epochs):
        z = X @ w + b
        p = 1.0 / (1.0 + np.exp(-z))
        g = p - y_bin
        gw = X.T @ g / n + l2 * w
        gb = g.mean()
        w -= lr * gw
        b -= lr * gb
    return w, b


def predict_logistic(X, w, b):
    return 1.0 / (1.0 + np.exp(-(X @ w + b)))


def accuracy(p, y_bin):
    return float(np.mean((p >= 0.5).astype(float) == y_bin))


class ModelRegistry:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.entries = []
        if os.path.exists(path):
            self.entries = json.load(open(path, encoding="utf-8")).get("models", [])

    def register(self, *, model_version, feature_schema_hash, label_schema_hash,
                 training_data_hash, code_commit, config_hash, metrics, artifact_path):
        entry = {
            "model_version": model_version,
            "feature_schema_hash": feature_schema_hash,
            "label_schema_hash": label_schema_hash,
            "training_data_hash": training_data_hash,
            "code_commit": code_commit,
            "config_hash": config_hash,
            "metrics": metrics,
            "artifact": artifact_path,
        }
        self.entries.append(entry)
        json.dump({"schema": "v3_model_registry/1", "models": self.entries},
                  open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return entry


def training_data_hash(X, y) -> str:
    return _hash({"X": _hash(X.tolist()), "y": _hash(y.tolist()), "shape": list(X.shape)})
