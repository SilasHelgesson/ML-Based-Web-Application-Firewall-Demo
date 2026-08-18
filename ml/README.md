# SQLi detection — ML pipeline

The classifier behind the filtering proxy. Runtime interface is a single call:

```python
from model import SqliDetector

detector = SqliDetector("sqli_model.joblib", threshold=0.9)   # ONCE at start-up

result = detector.predict(user_supplied_value)
# -> {"is_attack": bool, "label": str, "confidence": float, "attack_probability": float}
if result["is_attack"]:
    ...  # block / 403 / log
```

Use `predict_batch([...])` when one request has several fields to inspect —
per-item cost drops from ~1.8 ms to ~0.18 ms.

## Files

| file | what it is |
|---|---|
| `sqli_features.py` | Shared feature extraction: the URL-decode/lowercase normalizer and the handcrafted numeric features. **Imported by both training and the detector.** |
| `dataset.py` | `load_csv()` for real data, `make_synthetic()` for a scaffold set. |
| `model.py` | Builds the `FeatureUnion[char-TFIDF + handcrafted] → classifier` pipeline; defines the runtime `SqliDetector`. |
| `train.py` | CLI: train, evaluate, threshold sweep, latency benchmark, save. |
| `evaluate_model.py` | CLI: score a saved model against a dataset. Handles single-class sets (e.g. all-attack adversarial data). |
| `sqli_model.joblib` | The shipped model — logistic regression trained on SQLiV3. |
| `results/training_run.txt` | Recorded output of both reference runs. |

> [!NOTE]
> joblib pickles `HandcraftedFeatures` by module path, so `sqli_features` has
> to be importable as a **top-level** module wherever the model is loaded.
> That is why `proxy/main.py` puts `ml/` on `sys.path` rather than importing
> the pipeline as a package.

## Features

Two branches, concatenated by `FeatureUnion`:

1. **char n-gram TF-IDF**, `ngram_range=(1,5)`, `max_features=30000`, over the
   normalized text. `normalize()` URL-decodes twice (so `%2527` → `%27` → `'`),
   lowercases and strips. Character n-grams catch sub-token signals like `1=1`,
   `--`, `/**/` and survive inline-comment obfuscation (`uni/**/on`).
2. **16 handcrafted numeric features** over the raw text: length, special-char
   count and ratio, quote/equals/semicolon/paren/percent counts, digit ratio,
   SQL keyword count, comment-marker count, hex-literal flag, tautology flag,
   Shannon entropy, space count. Scaled with `MaxAbsScaler`. Encoding artefacts
   (many `%`, high entropy) remain visible here even before decoding.

Default classifier is logistic regression — microsecond inference and
calibrated probabilities. `--model rf` switches to a random forest, which
exposes feature importances if you want them for a write-up.

## Train

```bash
# real dataset (SQLiV3 has no header row, so pass column indexes):
python train.py --data data/SQLiV3.csv --text-col 0 --label-col 1

# synthetic scaffold, no data needed — checks the pipeline runs end to end:
python train.py

# random forest instead of logistic regression:
python train.py --data data/SQLiV3.csv --text-col 0 --label-col 1 --model rf
```

`load_csv` accepts column *names* or integer *indexes*, and maps labels from
`0/1` or strings (`benign`/`malicious`, `normal`/`sqli`, …). Rows with an
unrecognised label or empty text are dropped and counted. Output goes to
`sqli_model.joblib` (`--out` to change), `--seed` fixes the split and the
classifier's `random_state`.

The synthetic generator is only a scaffold — it scores ~1.0 on everything
because the generated classes are far too separable. It proves the pipeline
runs; it says nothing about real performance.

## Evaluate

```bash
python evaluate_model.py --model sqli_model.joblib --data data/fuzzed_data.csv
```

With both classes present you get a classification report, confusion matrix and
ROC/PR-AUC. With a single class (the adversarial set is all attacks) you get
detection rate across thresholds plus the lowest-scoring misses.

## Results

Logistic regression, SQLiV3, 75/25 stratified split (7,716 test samples):

| metric | value |
|---|---|
| accuracy | 0.998 |
| precision / recall / F1 (attack) | 0.996 / 0.997 / 0.997 |
| ROC-AUC / PR-AUC | 0.9993 / 0.9968 |
| false positives / false negatives | 10 / 9 |
| fit time | 5.8 s |
| latency | 1.82 ms mean, 1.76 ms median, 2.35 ms p95, 2.89 ms p99 |

Threshold sweep on the attack class:

| threshold | precision | recall | F1 |
|---|---|---|---|
| 0.30 | 0.995 | 0.998 | 0.996 |
| 0.50 | 0.996 | 0.997 | 0.997 |
| 0.70 | 0.998 | 0.994 | 0.996 |
| 0.90 | 0.998 | 0.983 | 0.991 |

The proxy runs at 0.9 — on this data that trades ~1.4 points of recall for the
lowest false-positive rate, which matters more when every false positive is a
blocked legitimate user.

**Adversarial robustness.** 9,627 WAF-A-MoLE payloads held out of training
(octal/binary/hex literals, exotic whitespace, case mangling):

| threshold | detection rate |
|---|---|
| 0.30 | 97.90% |
| 0.50 | 97.11% |
| 0.70 | 96.10% |
| 0.90 | 93.94% |

Mean P(malicious) = 0.967.

### Known gaps

The ~3% that slip through are mostly:

- **bare SQL keywords with no injection syntax** — `SeLECt`, `PROCEDure`,
  `OrDER\tBY`. There is nothing injection-shaped about them, and training the
  model to flag the word "select" on its own would cost false positives on
  ordinary text.
- **encodings `normalize()` doesn't undo** — vertical tab `\x0b`, form feed
  `\x0c`, non-breaking space `\xa0`, octal and binary numeric literals.

Worth fixing next: strip `\t\f\r\v\xa0` and decode octal/hex/binary literals in
`normalize()` before n-gramming. Also worth trying: scoring each parameter
separately instead of the concatenated payload, so one long benign field can't
dilute a short malicious one.

## Data

See [`data/README.md`](data/README.md) for provenance and licensing.
