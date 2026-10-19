"""Histograma con privacidad diferencial sobre uno o varios datasets (CSV o JSON).

Cada dataset (por ejemplo, una boya de un dueño distinto) aporta sus lecturas de una columna. El
algoritmo recorta los valores a [`lower`, `upper`], los cuenta en `bins` intervalos y añade a cada
cuenta ruido de Laplace de escala 1/ε. Cada lectura cae en un solo intervalo, así que la
sensibilidad es 1 y el histograma de cada dataset es ε-diferencialmente privado. La media
también se publica con ruido: ε se reparte a partes iguales entre la suma y la cuenta.

Lo que sale del nodo es solo el agregado con ruido: ninguna lectura individual. Con ε pequeño
(0,1) el ruido se ve a simple vista; con ε grande (10) el histograma casi no cambia.

Parámetros:
- `column` (text, por defecto `sea_surface_temp_c`)
- `epsilon` (number, por defecto 1)
- `bins` (number, por defecto 16)
- `lower` (number, por defecto 15)
- `upper` (number, por defecto 35)

Salida: /data/outputs/dp-histogram.json y /data/outputs/dp-histogram.svg
"""

import csv
import io
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import input_files, number, parameters, write_json, write_text  # noqa: E402

# Ruido de un generador del sistema: con una semilla conocida, el ruido se podría restar.
_rng = random.SystemRandom()
PALETTE = ["#1971c2", "#e8590c", "#2f9e44", "#ae3ec9", "#f08c00"]


def laplace(scale: float) -> float:
    u = _rng.random() - 0.5
    return -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))


def rows(path: Path) -> list[dict[str, object]]:
    """Las filas de un CSV con cabecera, o de un JSON: una lista de objetos o `{"records": [...]}`
    (el formato de las boyas de datos.rekodes.com)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.lstrip()[:1] in "[{":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        data = data.get("records", []) if isinstance(data, dict) else data
        return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []
    return list(csv.DictReader(io.StringIO(text)))


def read_column(path: Path, column: str) -> list[float]:
    values: list[float] = []
    for row in rows(path):
        try:
            values.append(float(row[column]))  # type: ignore[arg-type]
        except (KeyError, TypeError, ValueError):
            continue
    return values


def private_histogram(values: list[float], edges: list[float], epsilon: float) -> list[float]:
    bins = len(edges) - 1
    lower, upper = edges[0], edges[-1]
    width = (upper - lower) / bins
    counts = [0] * bins
    for v in values:
        clipped = min(max(v, lower), upper)
        counts[min(int((clipped - lower) / width), bins - 1)] += 1
    # Lo que se publica nunca es negativo; redondear después del ruido no gasta privacidad.
    return [max(0.0, round(c + laplace(1 / epsilon), 1)) for c in counts]


def private_mean(values: list[float], lower: float, upper: float, epsilon: float) -> float | None:
    clipped = [min(max(v, lower), upper) for v in values]
    bound = max(abs(lower), abs(upper))
    noisy_sum = sum(clipped) + laplace(bound / (epsilon / 2))
    noisy_count = len(clipped) + laplace(1 / (epsilon / 2))
    return round(noisy_sum / noisy_count, 2) if noisy_count >= 1 else None


def chart_svg(edges: list[float], series: dict[str, list[float]], column: str, epsilon: float) -> str:
    """Barras apiladas por dataset, una por intervalo."""
    width, height, left, bottom = 720, 320, 48, 36
    plot_w, plot_h = width - left - 16, height - bottom - 40
    bins = len(edges) - 1
    totals = [sum(s[i] for s in series.values()) for i in range(bins)]
    top = max(totals) or 1
    bar = plot_w / bins
    shapes = []
    for i in range(bins):
        y = 40 + plot_h
        for k, (name, counts) in enumerate(series.items()):
            h = plot_h * counts[i] / top
            y -= h
            shapes.append(
                f'<rect x="{left + i * bar + 1:.1f}" y="{y:.1f}" width="{bar - 2:.1f}" height="{h:.1f}" '
                f'fill="{PALETTE[k % len(PALETTE)]}"><title>{name}: {counts[i]}</title></rect>'
            )
        if i % 2 == 0:
            shapes.append(
                f'<text x="{left + i * bar:.1f}" y="{height - 14}" class="a">{edges[i]:g}</text>'
            )
    legend = "".join(
        f'<rect x="{left + k * 150}" y="10" width="12" height="12" fill="{PALETTE[k % len(PALETTE)]}"/>'
        f'<text x="{left + k * 150 + 18}" y="21" class="a">{name}</text>'
        for k, name in enumerate(series)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Histograma de {column} con ε={epsilon:g}">'
        "<style>.a{font:12px system-ui,sans-serif;fill:#6b6b76}</style>"
        f'<rect width="{width}" height="{height}" fill="#fff"/>{legend}{"".join(shapes)}'
        f'<text x="{width - 16}" y="21" text-anchor="end" class="a">{column} · ε = {epsilon:g}</text>'
        "</svg>\n"
    )


def main() -> int:
    params = parameters()
    column = str(params.get("column") or "sea_surface_temp_c")
    epsilon = number(params, "epsilon", 1.0)
    bins = int(number(params, "bins", 16))
    lower, upper = number(params, "lower", 15.0), number(params, "upper", 35.0)
    if epsilon <= 0 or bins < 2 or upper <= lower:
        print("Parámetros no válidos: epsilon > 0, bins >= 2 y upper > lower")
        return 2
    edges = [lower + (upper - lower) * i / bins for i in range(bins + 1)]

    sites = {}
    series = {}
    for path in input_files():
        values = read_column(path, column)
        if not values:
            print(f"{path.name}: sin la columna {column}, se ignora")
            continue
        series[path.stem] = private_histogram(values, edges, epsilon)
        sites[path.stem] = {"mean": private_mean(values, lower, upper, epsilon)}
        print(f"{path.name}: histograma y media publicados con ε={epsilon:g}")
    if not series:
        print("Ningún dataset tiene la columna pedida")
        return 1

    combined = [round(sum(s[i] for s in series.values()), 1) for i in range(bins)]
    write_json("dp-histogram.json", {
        "column": column,
        "epsilon_per_dataset": epsilon,
        "mechanism": "Laplace, sensibilidad 1 por lectura; la media reparte ε entre suma y cuenta",
        "edges": [round(e, 4) for e in edges],
        "datasets": {name: {"counts": counts, **sites[name]} for name, counts in series.items()},
        "combined_counts": combined,
    })
    write_text("dp-histogram.svg", chart_svg(edges, series, column, epsilon))
    return 0


if __name__ == "__main__":
    sys.exit(main())
