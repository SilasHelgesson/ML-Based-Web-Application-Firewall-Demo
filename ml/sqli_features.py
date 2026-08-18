# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from __future__ import annotations

import math
import re
import urllib.parse

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

def normalize(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    decoded = text
    # Two passes undo double URL-encoding: %2527 -> %27 -> '
    # (deeper nesting is not decoded; see 'Known gaps' in ml/README.md)
    for _ in range(2):
        new = urllib.parse.unquote_plus(decoded)
        if new == decoded:
            break
        decoded = new
    return decoded.lower().strip()

SQL_KEYWORDS = [
    "select", "union", "insert", "update", "delete", "drop", "alter", "create",
    "exec", "execute", "from", "where", "having", "join", "into", "table",
    "database", "sleep", "benchmark", "waitfor", "delay", "load_file", "outfile",
    "information_schema", "sqlite_master", "pg_sleep", "randomblob", "concat",
    "substring", "substr", "version", "cast", "convert", "extractvalue",
    "updatexml", "group_concat", "char", "ascii", "hex", "and", "or",
]

_kw_pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in SQL_KEYWORDS) + r")\b")
_comment_pattern = re.compile(r"(--|#|/\*|\*/)")
_hex_pattern = re.compile(r"0x[0-9a-f]+")
_taut_word = re.compile(r"\b(\w+)\s*=\s*\1\b")          # 1=1, a=a
_taut_quote = re.compile(r"(['\"]).*?\1\s*=\s*(['\"]).*?\2")  # 'x'='x'


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _has_tautology(norm: str) -> float:
    if _taut_word.search(norm) or _taut_quote.search(norm):
        return 1.0
    return 0.0


class HandcraftedFeatures(BaseEstimator, TransformerMixin):
    feature_names_ = [
        "length",
        "n_special",
        "ratio_special",
        "n_single_quote",
        "n_double_quote",
        "n_equals",
        "n_semicolon",
        "n_paren",
        "n_percent",
        "ratio_digit",
        "n_keywords",
        "n_comment_markers",
        "has_hex",
        "has_tautology",
        "entropy",
        "n_spaces",
    ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for raw in X:
            if not isinstance(raw, str):
                raw = str(raw)
            norm = normalize(raw)
            length = len(raw) or 1
            specials = sum(raw.count(c) for c in "'\";=()<>|&%-/*")
            digits = sum(ch.isdigit() for ch in raw)
            rows.append([
                len(raw),
                specials,
                specials / length,
                raw.count("'"),
                raw.count('"'),
                raw.count("="),
                raw.count(";"),
                raw.count("(") + raw.count(")"),
                raw.count("%"),
                digits / length,
                len(_kw_pattern.findall(norm)),
                len(_comment_pattern.findall(norm)),
                1.0 if _hex_pattern.search(norm) else 0.0,
                _has_tautology(norm),
                _shannon_entropy(raw),
                raw.count(" "),
            ])
        return np.asarray(rows, dtype=float)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_, dtype=object)
