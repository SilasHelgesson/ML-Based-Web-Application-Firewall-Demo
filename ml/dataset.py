# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from __future__ import annotations

import random
import urllib.parse

import pandas as pd

def load_csv(path: str, text_col="payload", label_col="label"):
    def _as_int(x):
        try:
            return int(str(x).strip())
        except (TypeError, ValueError):
            return None

    ti, li = _as_int(text_col), _as_int(label_col)

    if ti is not None and li is not None:
        df = pd.read_csv(path, header=None, engine="python",
                         on_bad_lines="skip", dtype=str, keep_default_na=False)
        ncols = df.shape[1]
        if ti >= ncols or li >= ncols:
            raise ValueError(
                f"File has {ncols} columns (valid indexes 0..{ncols - 1}); "
                f"you asked for text-col {ti} and label-col {li}."
            )
        text_series = df.iloc[:, ti].astype(str)
        label_series = df.iloc[:, li].astype(str)
    else:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        missing = [c for c in (text_col, label_col) if c not in df.columns]
        if missing:
            raise ValueError(
                f"Column(s) {missing} not found. CSV columns are {list(df.columns)}. "
                f"Pass names from that list, or integer indexes "
                f"(e.g. --text-col 0 --label-col 1) if the file has no header row."
            )
        text_series = df[text_col].astype(str)
        label_series = df[label_col].astype(str)

    pos = {"1", "malicious", "sqli", "attack", "injection", "anomalous", "bad", "true"}
    neg = {"0", "benign", "normal", "legit", "legitimate", "valid", "good", "false", "plain"}

    texts, labels, dropped_label, dropped_empty = [], [], 0, 0
    for t, raw_l in zip(text_series, label_series):
        l = raw_l.strip().lower()
        if l in pos:
            y = 1
        elif l in neg:
            y = 0
        else:
            dropped_label += 1
            continue
        t = t.strip()
        if not t:
            dropped_empty += 1
            continue
        texts.append(t)
        labels.append(y)
    return texts, labels


# --------------------------------------------------------------------------- #
# synthetic data
# --------------------------------------------------------------------------- #
_FIRST = ["james", "mary", "wei", "olga", "ahmed", "sofia", "liam", "noah",
          "emma", "yuki", "diego", "fatima", "lukas", "anna", "raj", "chloe"]
_LAST = ["smith", "o'brien", "d'angelo", "müller", "nguyen", "garcia", "kim",
         "rossi", "novak", "andersson", "khan", "dubois", "o'connor"]
_DOMAINS = ["gmail.com", "tu-berlin.de", "outlook.com", "proton.me", "web.de"]
_WORDS = ["laptop", "blue shoes", "running", "best price", "winter jacket",
          "python tutorial", "cheap flights berlin", "coffee machine",
          "the great gatsby", "order status", "return policy", "size medium"]
_SENTENCES = [
    "I would like to select option 3 from the menu",
    "Please update my shipping address to the new one",
    "Can I order this in a different colour?",
    "The product I want is out of stock, when does it return?",
    "I joined the loyalty program last week",
    "Where do I insert the discount code at checkout?",
    "My table reservation is for two people at 7pm",
]


def _benign(rng: random.Random) -> str:
    kind = rng.random()
    if kind < 0.20:
        return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}".title()
    if kind < 0.35:
        u = f"{rng.choice(_FIRST)}.{rng.choice(_LAST).replace(chr(39), '')}"
        return f"{u}@{rng.choice(_DOMAINS)}"
    if kind < 0.50:
        return str(rng.randint(1, 999999))
    if kind < 0.62:
        return f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"
    if kind < 0.80:
        return rng.choice(_WORDS)
    if kind < 0.92:
        return rng.choice(_SENTENCES)
    # hard negatives: legitimate text that happens to contain quotes / sql words
    hard = [
        "O'Brien", "d'Angelo & Sons Ltd.", "rock 'n' roll",
        "I want to order by date, newest first",   # contains 'order by'
        "she said \"hello\" and left",
        "50% off selected items",                   # contains 'select'
        "drop me an email when it ships",           # contains 'drop'
        "1 = one in the count",
    ]
    return rng.choice(hard)


_SQLI_BASES = [
    "' OR 1=1 --",
    "' OR '1'='1",
    "admin' --",
    "admin' #",
    "' OR 1=1 #",
    "1' OR '1'='1' --",
    "') OR ('1'='1",
    "' UNION SELECT NULL, username, password FROM users --",
    "' UNION SELECT NULL,NULL,NULL --",
    "1 UNION SELECT user, password FROM accounts",
    "'; DROP TABLE users; --",
    "'; DELETE FROM sessions; --",
    "' AND 1=0 UNION SELECT credit_card, cvv FROM payments --",
    "' OR SLEEP(5) --",
    "' OR pg_sleep(5) --",
    "'; WAITFOR DELAY '0:0:5' --",
    "' AND 1=CAST((SELECT version()) AS int) --",
    "' AND extractvalue(1, concat(0x7e, version())) --",
    "' AND substring(version(),1,1)='5",
    "' AND ascii(substr(database(),1,1))>64 --",
    "' UNION SELECT name, sql FROM sqlite_master --",       # sqlite
    "' OR 1=randomblob(100000000) --",                       # sqlite DoS
    "' UNION SELECT NULL, sqlite_version() --",              # sqlite
    "1; ATTACH DATABASE '/tmp/x.db' AS x --",                # sqlite
    "%27%20OR%201%3D1%20--",                                 # already url-encoded
    "' OR 'a'='a' /*",
]


def _mutate(payload: str, rng: random.Random) -> str:
    """Apply random obfuscations to a base payload."""
    out = payload

    # case randomization on letters
    if rng.random() < 0.5:
        out = "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in out)

    # inline-comment obfuscation: replace some spaces with /**/
    if rng.random() < 0.4:
        out = out.replace(" ", "/**/", rng.randint(1, 3))

    # split a keyword with an inline comment, e.g. UNION -> UN/**/ION
    if rng.random() < 0.3:
        for kw in ("union", "select", "where", "from"):
            i = out.lower().find(kw)
            if i != -1:
                mid = i + len(kw) // 2
                out = out[:mid] + "/**/" + out[mid:]
                break

    # whitespace padding
    if rng.random() < 0.3:
        out = out.replace(" ", "  " if rng.random() < 0.5 else "\t")

    # url-encode a subset of chars (and sometimes double-encode)
    if rng.random() < 0.45:
        enc = out.replace("'", "%27").replace(" ", "%20").replace("=", "%3D")
        if rng.random() < 0.3:
            enc = urllib.parse.quote(enc)  # double-encode
        out = enc

    return out


def make_synthetic(n: int = 8000, seed: int = 0, malicious_ratio: float = 0.4):
    """Generate a synthetic benign/malicious set.

    Sanity-checks that the pipeline runs end to end without needing a download.
    The two classes are far too separable to say anything about real
    performance -- always report numbers from a real dataset.
    """
    rng = random.Random(seed)
    texts, labels = [], []
    for _ in range(n):
        if rng.random() < malicious_ratio:
            texts.append(_mutate(rng.choice(_SQLI_BASES), rng))
            labels.append(1)
        else:
            texts.append(_benign(rng))
            labels.append(0)
    return texts, labels


def write_synthetic_csv(path: str, n: int = 8000, seed: int = 0) -> str:
    """Dump a synthetic set to CSV with `payload`/`label` columns."""
    texts, labels = make_synthetic(n=n, seed=seed)
    pd.DataFrame({"payload": texts, "label": labels}).to_csv(path, index=False)
    return path
