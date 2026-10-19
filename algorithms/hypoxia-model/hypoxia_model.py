"""Entrena un modelo de hipoxia con los datos de una o varias boyas, sin que salgan del nodo.

Regresión logística en Python puro (sin numpy) sobre las variables de las boyas sintéticas de
datos.rekodes.com (`boyas-hipoxia`). Las variables se estandarizan y se entrena por descenso de
gradiente. La prueba es el último 20 % de horas de cada boya, para no mezclar pasado y futuro.
Es el entrenamiento local que el aprendizaje federado repetirá en cada nodo (fase 6): lo que sale
son los pesos y las métricas, no las lecturas.

Parámetros: `epochs` (number, 300), `learning_rate` (number, 0.5) y `l2` (number, 0.001).
Salida: /data/outputs/model.json, /data/outputs/metrics.json y /data/outputs/coefficients.svg
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import input_files, number, parameters, write_json, write_text  # noqa: E402

FEATURES = ["sea_surface_temp_c", "salinity_psu", "chlorophyll_mg_m3", "wind_speed_m_s", "wave_height_m"]
TARGET = "hypoxia"


def load(path: Path) -> list[dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    rows = data.get("records", []) if isinstance(data, dict) else data
    return [r for r in rows if isinstance(r, dict) and TARGET in r and all(f in r for f in FEATURES)]


def split(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows = sorted(rows, key=lambda r: str(r.get("timestamp", "")))
    cut = int(len(rows) * 0.8)
    return rows[:cut], rows[cut:]


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def standardise(rows, means, stds) -> list[list[float]]:  # type: ignore[no-untyped-def]
    return [[(float(r[f]) - means[i]) / stds[i] for i, f in enumerate(FEATURES)] for r in rows]


def train(x: list[list[float]], y: list[int], epochs: int, rate: float, l2: float) -> tuple[list[float], float]:
    weights = [0.0] * len(FEATURES)
    bias = 0.0
    n = len(x)
    for _ in range(epochs):
        grad_w = [0.0] * len(weights)
        grad_b = 0.0
        for xi, yi in zip(x, y, strict=True):
            error = sigmoid(sum(w * v for w, v in zip(weights, xi, strict=True)) + bias) - yi
            for j, v in enumerate(xi):
                grad_w[j] += error * v
            grad_b += error
        weights = [w - rate * (g / n + l2 * w) for w, g in zip(weights, grad_w, strict=True)]
        bias -= rate * grad_b / n
    return weights, bias


def metrics(x, y, weights, bias) -> dict[str, float]:  # type: ignore[no-untyped-def]
    scores = [sigmoid(sum(w * v for w, v in zip(weights, xi, strict=True)) + bias) for xi in x]
    pred = [int(s >= 0.5) for s in scores]
    tp = sum(1 for p, t in zip(pred, y, strict=True) if p and t)
    fp = sum(1 for p, t in zip(pred, y, strict=True) if p and not t)
    fn = sum(1 for p, t in zip(pred, y, strict=True) if not p and t)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    # AUC por pares: la probabilidad de que un positivo puntúe más que un negativo.
    pos = [s for s, t in zip(scores, y, strict=True) if t]
    neg = [s for s, t in zip(scores, y, strict=True) if not t]
    auc = (sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))) if pos and neg else 0.0
    return {
        "accuracy": round(sum(p == t for p, t in zip(pred, y, strict=True)) / len(y), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "auc": round(auc, 4),
        "positives": len(pos),
        "samples": len(y),
    }


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


def main() -> int:
    params = parameters()
    epochs = int(number(params, "epochs", 300))
    rate = number(params, "learning_rate", 0.5)
    l2 = number(params, "l2", 0.001)
    train_rows: list[dict[str, object]] = []
    test_rows: list[dict[str, object]] = []
    sources = []
    for path in input_files():
        rows = load(path)
        if not rows:
            print(f"{path.name}: no tiene las variables de las boyas, se ignora")
            continue
        a, b = split(rows)
        train_rows += a
        test_rows += b
        sources.append({"file": path.name, "rows": len(rows)})
    if not train_rows or not test_rows:
        print("No hay datos de boyas con los que entrenar")
        return 1

    means = [sum(float(r[f]) for r in train_rows) / len(train_rows) for f in FEATURES]
    stds = [
        math.sqrt(sum((float(r[f]) - means[i]) ** 2 for r in train_rows) / len(train_rows)) or 1.0
        for i, f in enumerate(FEATURES)
    ]
    y_train = [int(bool(r[TARGET])) for r in train_rows]
    y_test = [int(bool(r[TARGET])) for r in test_rows]
    weights, bias = train(standardise(train_rows, means, stds), y_train, epochs, rate, l2)
    result = metrics(standardise(test_rows, means, stds), y_test, weights, bias)

    write_json("model.json", {
        "kind": "logistic_regression", "features": FEATURES, "target": TARGET,
        "weights": [round(w, 6) for w in weights], "bias": round(bias, 6),
        "standardisation": {"means": [round(m, 6) for m in means], "stds": [round(s, 6) for s in stds]},
        "hyperparameters": {"epochs": epochs, "learning_rate": rate, "l2": l2},
    })
    write_json("metrics.json", {"test": result, "train_samples": len(train_rows), "sources": sources})
    write_text("coefficients.svg", coefficients_svg(weights))
    print(f"Entrenado con {len(train_rows)} horas de {len(sources)} boyas; prueba con {len(test_rows)}")
    print(f"Exactitud {result['accuracy']}, F1 {result['f1']}, AUC {result['auc']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
