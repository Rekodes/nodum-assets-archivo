"""Regresión logística que predice la hipoxia con los datos de las boyas, sin que salgan del nodo.

Python puro (sin numpy). Variables estandarizadas y descenso de gradiente con L2. La prueba es el
último 20 % de horas de cada boya. Es el entrenamiento local del aprendizaje federado: salen los
pesos y las métricas, no las lecturas.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from ocean_app import Algorithm, AlgorithmError, Job, Parameter, Record, main, read_records

log = logging.getLogger(__name__)

FEATURES = ("sea_surface_temp_c", "salinity_psu", "chlorophyll_mg_m3", "wind_speed_m_s", "wave_height_m")
TARGET = "hypoxia"
TEST_SHARE = 0.2

Matrix = list[list[float]]


def feature(row: Record, name: str) -> float:
    value = row[name]
    if not isinstance(value, (int, float, str)):
        raise TypeError(f"{name}: {value!r} no es un número")
    return float(value)


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


@dataclass(frozen=True)
class Standardiser:
    means: list[float]
    stds: list[float]

    @classmethod
    def fit(cls, rows: list[Record]) -> Standardiser:
        n = len(rows)
        means = [sum(feature(r, f) for r in rows) / n for f in FEATURES]
        stds = [
            math.sqrt(sum((feature(r, f) - means[i]) ** 2 for r in rows) / n) or 1.0 for i, f in enumerate(FEATURES)
        ]
        return cls(means, stds)

    def transform(self, rows: list[Record]) -> Matrix:
        return [
            [(feature(r, f) - self.means[i]) / self.stds[i] for i, f in enumerate(FEATURES)] for r in rows
        ]


class LogisticRegression:
    def __init__(self, epochs: int, learning_rate: float, l2: float) -> None:
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.l2 = l2
        self.weights = [0.0] * len(FEATURES)
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


class HypoxiaModel(Algorithm):
    parameters = (
        Parameter("epochs", "number", "Épocas", "Pasadas del descenso de gradiente.", default=300),
        Parameter("learning_rate", "number", "Tasa de aprendizaje", "Tamaño del paso.", default=0.5),
        Parameter("l2", "number", "Regularización L2", "Penaliza los pesos grandes.", default=0.001),
    )

    def run(self, job: Job) -> None:
        train_rows: list[Record] = []
        test_rows: list[Record] = []
        sources = []
        for path in job.inputs:
            rows = [r for r in read_records(path) if TARGET in r and all(f in r for f in FEATURES)]
            if not rows:
                log.info("%s: no tiene las variables de las boyas, se ignora", path.name)
                continue
            train, test = self._split(rows)
            train_rows += train
            test_rows += test
            sources.append({"file": path.name, "rows": len(rows)})
        if not train_rows or not test_rows:
            raise AlgorithmError("No hay datos de boyas con los que entrenar")

        scaler = Standardiser.fit(train_rows)
        model = LogisticRegression(
            job.parameters.integer("epochs"), job.parameters.number("learning_rate"), job.parameters.number("l2")
        )
        model.fit(scaler.transform(train_rows), [self._label(r) for r in train_rows])
        metrics = evaluate(model, scaler.transform(test_rows), [self._label(r) for r in test_rows])

        job.outputs.write_json("model.json", {
            "kind": "logistic_regression",
            "features": list(FEATURES),
            "target": TARGET,
            "weights": [round(w, 6) for w in model.weights],
            "bias": round(model.bias, 6),
            "standardisation": {"means": [round(m, 6) for m in scaler.means],
                                "stds": [round(s, 6) for s in scaler.stds]},
            "hyperparameters": {"epochs": model.epochs, "learning_rate": model.learning_rate, "l2": model.l2},
        })
        job.outputs.write_json("metrics.json", {"test": metrics, "train_samples": len(train_rows), "sources": sources})
        job.outputs.write_text("coefficients.svg", coefficients_svg(model.weights))
        log.info("Entrenado con %d horas de %d boyas; prueba con %d", len(train_rows), len(sources), len(test_rows))
        log.info("Exactitud %s, F1 %s, AUC %s", metrics["accuracy"], metrics["f1"], metrics["auc"])

    @staticmethod
    def _split(rows: list[Record]) -> tuple[list[Record], list[Record]]:
        """Por orden de tiempo, para no mezclar pasado y futuro."""
        rows = sorted(rows, key=lambda r: str(r.get("timestamp", "")))
        cut = int(len(rows) * (1 - TEST_SHARE))
        return rows[:cut], rows[cut:]

    @staticmethod
    def _label(row: Record) -> int:
        value = row[TARGET]
        if isinstance(value, str):
            return int(value.strip().lower() in {"true", "1"})
        return int(bool(value))


def coefficients_svg(weights: list[float]) -> str:
    top = max(abs(w) for w in weights) or 1
    rows = []
    for i, (name, w) in enumerate(zip(FEATURES, weights, strict=True)):
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
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 180" role="img" '
        'aria-label="Coeficientes del modelo de hipoxia">'
        "<style>.a{font:12px system-ui,sans-serif;fill:#3b3b45}</style>"
        '<rect width="620" height="180" fill="#fff"/><line x1="380" y1="8" x2="380" y2="170" stroke="#ccc"/>'
        f'{"".join(rows)}</svg>\n'
    )


if __name__ == "__main__":
    main(HypoxiaModel())
