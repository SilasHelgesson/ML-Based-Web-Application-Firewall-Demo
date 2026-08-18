# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from __future__ import annotations

import argparse

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

import dataset
from model import SqliDetector


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sqli_model.joblib")
    ap.add_argument("--data", required=True)
    ap.add_argument("--text-col", default="payload")
    ap.add_argument("--label-col", default="label")
    args = ap.parse_args()

    texts, labels = dataset.load_csv(args.data, args.text_col, args.label_col)
    labels = np.array(labels)
    det = SqliDetector(args.model)
    probs = np.array([r["attack_probability"] for r in det.predict_batch(texts)])

    n_classes = len(set(labels.tolist()))
    print(f"{len(texts)} samples | classes present: {sorted(set(labels.tolist()))}")

    if n_classes == 2:
        preds = (probs >= 0.5).astype(int)
        print("\n=== Classification report (threshold 0.5) ===")
        print(classification_report(labels, preds,
                                    target_names=["benign", "malicious"], digits=3))
        cm = confusion_matrix(labels, preds)
        print("Confusion [rows=true, cols=pred]:")
        print(f"  benign     {cm[0,0]:>8} {cm[0,1]:>8}")
        print(f"  malicious  {cm[1,0]:>8} {cm[1,1]:>8}")
        print(f"\nROC-AUC: {roc_auc_score(labels, probs):.4f}  "
              f"PR-AUC: {average_precision_score(labels, probs):.4f}")
    else:
        only = labels[0]
        kind = "attacks (recall = detection rate)" if only == 1 else "benign (1 - FPR)"
        print(f"\nSingle-class set: all {kind}")
        for thr in (0.3, 0.5, 0.7, 0.9):
            if only == 1:
                rate = (probs >= thr).mean()
            else:
                rate = (probs < thr).mean()
            print(f"  threshold {thr:.2f}:  {rate*100:6.2f}%")
        print(f"\n  mean P(malicious): {probs.mean():.3f}")
        if only == 1:
            order = np.argsort(probs)[:8]
            print("  worst misses (lowest P(malicious)):")
            for i in order:
                print(f"    p={probs[i]:.3f}  {repr(texts[i][:70])}")


if __name__ == "__main__":
    main()
