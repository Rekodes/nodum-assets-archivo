"""Regresión logística en Python puro (sin numpy), para los modelos que entrenan dentro del nodo.

Variables estandarizadas y descenso de gradiente con L2. Es el entrenamiento local del aprendizaje
federado: lo que sale son pesos y métricas, nunca las filas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ocean_app import Record

Matrix = list[list[float]]


def feature(row: Record, name: str) -> float:
    value = row[name]
    if not isinstance(value, (int, float, str)):
        raise TypeError(f"{name}: {value!r} no es un número")
    return float(value)


def label(row: Record, target: str) -> int:
    value = row[target]
    if isinstance(value, str):
        return int(value.strip().lower() in {"true", "1"})
    return int(bool(value))


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def split_by_time(rows: list[Record], test_share: float) -> tuple[list[Record], list[Record]]:
    """Por orden de `timestamp`, para no entrenar con el futuro y probar con el pasado."""
    rows = sorted(rows, key=lambda r: str(r.get("timestamp", "")))
    cut = int(len(rows) * (1 - test_share))
    return rows[:cut], rows[cut:]


@dataclass(frozen=True)
class Standardiser:
    features: tuple[str, ...]
    means: list[float]
    stds: list[float]

    @classmethod
    def fit(cls, features: tuple[str, ...], rows: list[Record]) -> Standardiser:
        n = len(rows)
        means = [sum(feature(r, f) for r in rows) / n for f in features]
        stds = [
            math.sqrt(sum((feature(r, f) - means[i]) ** 2 for r in rows) / n) or 1.0 for i, f in enumerate(features)
        ]
        return cls(features, means, stds)

    def transform(self, rows: list[Record]) -> Matrix:
        return [
            [(feature(r, f) - self.means[i]) / self.stds[i] for i, f in enumerate(self.features)] for r in rows
        ]


class LogisticRegression:
    def __init__(self, size: int, epochs: int, learning_rate: float, l2: float) -> None:
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.l2 = l2
        self.weights = [0.0] * size
        self.bias = 0.0

    def fit(self, x: Matrix, y: list[int]) -> None:
        n = len(x)
        for _ in range(self.epochs):
            grad_w = [0.0] * len(self.weights)
            grad_b = 0.0
            for xi, yi in zip(x, y, strict=True):
                error = self.score(xi) - yi
                for j, v in enumerate(xi):
                    grad_w[j] += error * v
                grad_b += error
            self.weights = [
                w - self.learning_rate * (g / n + self.l2 * w) for w, g in zip(self.weights, grad_w, strict=True)
            ]
            self.bias -= self.learning_rate * grad_b / n

    def score(self, xi: list[float]) -> float:
        return sigmoid(sum(w * v for w, v in zip(self.weights, xi, strict=True)) + self.bias)


def evaluate(model: LogisticRegression, x: Matrix, y: list[int]) -> dict[str, float]:
    scores = [model.score(xi) for xi in x]
    pred = [int(s >= 0.5) for s in scores]
    tp = sum(1 for p, t in zip(pred, y, strict=True) if p and t)
    fp = sum(1 for p, t in zip(pred, y, strict=True) if p and not t)
    fn = sum(1 for p, t in zip(pred, y, strict=True) if not p and t)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    # AUC por pares: probabilidad de que un positivo puntúe más que un negativo.
    pos = [s for s, t in zip(scores, y, strict=True) if t]
    neg = [s for s, t in zip(scores, y, strict=True) if not t]
    auc = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg)) if pos and neg else 0.0
    return {
        "accuracy": round(sum(p == t for p, t in zip(pred, y, strict=True)) / len(y), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "auc": round(auc, 4),
        "positives": len(pos),
        "samples": len(y),
    }


def model_document(target: str, scaler: Standardiser, model: LogisticRegression) -> dict[str, object]:
    return {
        "kind": "logistic_regression",
        "features": list(scaler.features),
        "target": target,
        "weights": [round(w, 6) for w in model.weights],
        "bias": round(model.bias, 6),
        "standardisation": {"means": [round(m, 6) for m in scaler.means], "stds": [round(s, 6) for s in scaler.stds]},
        "hyperparameters": {"epochs": model.epochs, "learning_rate": model.learning_rate, "l2": model.l2},
    }


def coefficients_svg(features: tuple[str, ...], weights: list[float], title: str) -> str:
    top = max(abs(w) for w in weights) or 1
    height = 20 + 30 * len(features)
    rows = []
    for i, (name, w) in enumerate(zip(features, weights, strict=True)):
        y = 16 + i * 30
        width = 180 * abs(w) / top
        x = 380 if w >= 0 else 380 - width
        fill = "#e03131" if w >= 0 else "#1971c2"
        rows.append(
            f'<text x="190" y="{y + 14}" text-anchor="end" class="a">{name}</text>'
            f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="18" fill="{fill}"/>'
            f'<text x="{(x + width + 6) if w >= 0 else (x - 6):.1f}" y="{y + 14}" '
            f'text-anchor="{"start" if w >= 0 else "end"}" class="a">{w:+.2f}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 {height}" role="img" aria-label="{title}">'
        "<style>.a{font:12px system-ui,sans-serif;fill:#3b3b45}</style>"
        f'<rect width="620" height="{height}" fill="#fff"/>'
        f'<line x1="380" y1="8" x2="380" y2="{height - 10}" stroke="#ccc"/>'
        f'{"".join(rows)}</svg>\n'
    )
