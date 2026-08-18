# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from __future__ import annotations

import argparse
import time

import joblib
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

import dataset
from model import build_pipeline


def _latency_benchmark(pipeline, texts, n=2000):
    sample = list(texts[:n]) if len(texts) >= n else list(texts)
    has_proba = hasattr(pipeline, "predict_proba")

    # 10 warmup runs (JIT, caching, etc.)
    for _ in range(10):
        _ = pipeline.predict_proba([sample[0]]) if has_proba else pipeline.predict([sample[0]])

    times = []
    for t in sample:
        start = time.perf_counter()
        if has_proba:
            pipeline.predict_proba([t])
        else:
            pipeline.predict([t])
        times.append((time.perf_counter() - start) * 1000.0)  # ms

    times = np.array(times)

    # batch throughput
    bstart = time.perf_counter()
    if has_proba:
        pipeline.predict_proba(sample)
    else:
        pipeline.predict(sample)
    batch_ms = (time.perf_counter() - bstart) * 1000.0

    return {
        "n": len(sample),
        "mean_ms": times.mean(),
        "median_ms": np.median(times),
        "p95_ms": np.percentile(times, 95),
        "p99_ms": np.percentile(times, 99),
        "batch_per_item_ms": batch_ms / len(sample),
    }


def _threshold_sweep(y_true, probs, thresholds=(0.3, 0.5, 0.7, 0.9)):
    print("\nThreshold sweep (precision/recall on the attack class):")
    print(f"  {'thr':>5} {'precision':>10} {'recall':>8} {'f1':>7}")
    for thr in thresholds:
        pred = (probs >= thr).astype(int)
        p, r, f, _ = precision_recall_fscore_support(
            y_true, pred, average="binary", zero_division=0
        )
        print(f"  {thr:>5.2f} {p:>10.3f} {r:>8.3f} {f:>7.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="CSV path; omit to use synthetic data")
    ap.add_argument("--text-col", default="payload")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--model", default="logreg", choices=["logreg", "rf"])
    ap.add_argument("--out", default="sqli_model.joblib")
    ap.add_argument("--n-synth", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=0,
                    help="random_state for the split and the classifier")
    args = ap.parse_args()

    if args.data:
        print(f"Loading data from {args.data} ...")
        texts, labels = dataset.load_csv(args.data, args.text_col, args.label_col)
    else:
        print(f"No --data given; generating {args.n_synth} synthetic samples.")
        texts, labels = dataset.make_synthetic(n=args.n_synth, seed=args.seed)

    labels = np.array(labels)
    print(f"Total: {len(texts)}  |  benign: {(labels==0).sum()}  malicious: {(labels==1).sum()}")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, stratify=labels, random_state=args.seed
    )

    print(f"\nTraining pipeline on {len(X_train)} samples ...")
    t0 = time.perf_counter()
    pipeline = build_pipeline(args.model, random_state=args.seed)
    pipeline.fit(X_train, y_train)
    print(f"  fit time: {time.perf_counter() - t0:.2f}s")

    # --- evaluation ---
    probs = pipeline.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    print("\n=== Classification report (threshold 0.5) ===")
    print(classification_report(y_test, preds, target_names=["benign", "malicious"], digits=3))

    cm = confusion_matrix(y_test, preds)
    print("Confusion matrix [rows=true, cols=pred]  (0=benign, 1=malicious):")
    print("            pred:benign  pred:malicious")
    print(f"  benign      {cm[0,0]:>8}      {cm[0,1]:>8}")
    print(f"  malicious   {cm[1,0]:>8}      {cm[1,1]:>8}")

    print(f"\nROC-AUC:  {roc_auc_score(y_test, probs):.4f}")
    print(f"PR-AUC :  {average_precision_score(y_test, probs):.4f}")

    _threshold_sweep(y_test, probs)

    # --- latency ---
    print("\n=== Per-request inference latency ===")
    lat = _latency_benchmark(pipeline, X_test)
    print(f"  samples timed : {lat['n']}")
    print(f"  mean          : {lat['mean_ms']:.4f} ms/request")
    print(f"  median        : {lat['median_ms']:.4f} ms/request")
    print(f"  p95           : {lat['p95_ms']:.4f} ms/request")
    print(f"  p99           : {lat['p99_ms']:.4f} ms/request")
    print(f"  batch per-item: {lat['batch_per_item_ms']:.4f} ms (if you batch)")

    joblib.dump(pipeline, args.out)
    print(f"\nSaved model -> {args.out}")


if __name__ == "__main__":
    main()
