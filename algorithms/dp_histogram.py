"""Histograma y media de una variable con privacidad diferencial (mecanismo de Laplace).

Cada lectura cae en un solo intervalo: sensibilidad 1, así que el histograma de cada dataset es
ε-diferencialmente privado. La media reparte ε entre la suma y la cuenta. Solo sale el agregado
con ruido, nunca una lectura.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from pathlib import Path

from ocean_app import Algorithm, AlgorithmError, InvalidParametersError, Job, Parameter, main, read_records

log = logging.getLogger(__name__)

PALETTE = ("#1971c2", "#e8590c", "#2f9e44", "#ae3ec9", "#f08c00")
BUOY_COLUMNS = ("sea_surface_temp_c", "salinity_psu", "chlorophyll_mg_m3", "dissolved_oxygen_mg_l",
                "wind_speed_m_s", "wave_height_m")


class LaplaceMechanism:
    """Ruido de Laplace de escala sensibilidad/ε. Sin semilla: con una conocida, se podría restar."""

    def __init__(self, epsilon: float, rng: random.Random | None = None) -> None:
        self.epsilon = epsilon
        self._rng = rng or random.SystemRandom()

    def noise(self, sensitivity: float, epsilon: float | None = None) -> float:
        scale = sensitivity / (epsilon or self.epsilon)
        u = self._rng.random() - 0.5
        return -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))


@dataclass(frozen=True)
class Bins:
    lower: float
    upper: float
    count: int

    @property
    def edges(self) -> list[float]:
        step = (self.upper - self.lower) / self.count
        return [self.lower + step * i for i in range(self.count + 1)]

    def clip(self, value: float) -> float:
        return min(max(value, self.lower), self.upper)

    def index(self, value: float) -> int:
        step = (self.upper - self.lower) / self.count
        return min(int((self.clip(value) - self.lower) / step), self.count - 1)


class PrivateSummary:
    """El histograma y la media de un dataset, con ruido."""

    def __init__(self, bins: Bins, mechanism: LaplaceMechanism) -> None:
        self._bins = bins
        self._mechanism = mechanism

    def histogram(self, values: list[float]) -> list[float]:
        counts = [0] * self._bins.count
        for value in values:
            counts[self._bins.index(value)] += 1
        # Nunca negativo; redondear después del ruido no gasta privacidad.
        return [max(0.0, round(c + self._mechanism.noise(1), 1)) for c in counts]

    def mean(self, values: list[float]) -> float | None:
        half = self._mechanism.epsilon / 2
        bound = max(abs(self._bins.lower), abs(self._bins.upper))
        noisy_sum = sum(self._bins.clip(v) for v in values) + self._mechanism.noise(bound, half)
        noisy_count = len(values) + self._mechanism.noise(1, half)
        return round(noisy_sum / noisy_count, 2) if noisy_count >= 1 else None


class DpHistogram(Algorithm):
    parameters = (
        Parameter("column", "select", "Variable", "Qué variable de las boyas se resume.",
                  default="sea_surface_temp_c", required=True, options=BUOY_COLUMNS),
        Parameter("epsilon", "number", "ε (privacidad)", "Más pequeño, más ruido y más privacidad.",
                  default=1, required=True),
        Parameter("bins", "number", "Intervalos", "Cuántas barras tiene el histograma.", default=16),
        Parameter("lower", "number", "Mínimo", "Los valores por debajo se recortan a este.", default=15),
        Parameter("upper", "number", "Máximo", "Los valores por encima se recortan a este.", default=35),
    )

    def run(self, job: Job) -> None:
        column = job.parameters.text("column")
        epsilon = job.parameters.number("epsilon")
        bins = Bins(job.parameters.number("lower"), job.parameters.number("upper"), job.parameters.integer("bins"))
        if epsilon <= 0 or bins.count < 2 or bins.upper <= bins.lower:
            raise InvalidParametersError("Parámetros no válidos: epsilon > 0, bins >= 2 y upper > lower")

        summary = PrivateSummary(bins, LaplaceMechanism(epsilon))
        summaries: dict[str, tuple[list[float], float | None]] = {}
        for path in job.inputs:
            values = self._column(path, column)
            if not values:
                log.info("%s: sin la columna %s, se ignora", path.name, column)
                continue
            summaries[path.stem] = (summary.histogram(values), summary.mean(values))
            log.info("%s: histograma y media publicados con ε=%g", path.name, epsilon)
        if not summaries:
            raise AlgorithmError("Ningún dataset tiene la columna pedida")

        series = {name: counts for name, (counts, _) in summaries.items()}
        job.outputs.write_json("dp-histogram.json", {
            "column": column,
            "epsilon_per_dataset": epsilon,
            "mechanism": "Laplace, sensibilidad 1 por lectura; la media reparte ε entre suma y cuenta",
            "edges": [round(e, 4) for e in bins.edges],
            "datasets": {name: {"counts": counts, "mean": mean} for name, (counts, mean) in summaries.items()},
            "combined_counts": [round(sum(s[i] for s in series.values()), 1) for i in range(bins.count)],
        })
        job.outputs.write_text("dp-histogram.svg", chart_svg(bins.edges, series, column, epsilon))

    @staticmethod
    def _column(path: Path, column: str) -> list[float]:
        values = []
        for row in read_records(path):
            try:
                values.append(float(row[column]))  # type: ignore[arg-type]
            except (KeyError, TypeError, ValueError):
                continue
        return values


def chart_svg(edges: list[float], series: dict[str, list[float]], column: str, epsilon: float) -> str:
    """Barras apiladas por dataset, una por intervalo."""
    width, height, left, bottom = 720, 320, 48, 36
    plot_w, plot_h = width - left - 16, height - bottom - 40
    bins = len(edges) - 1
    top = max(sum(s[i] for s in series.values()) for i in range(bins)) or 1.0
    bar = plot_w / bins
    shapes = []
    for i in range(bins):
        y: float = 40 + plot_h
        for k, (name, counts) in enumerate(series.items()):
            h = plot_h * counts[i] / top
            y -= h
            shapes.append(
                f'<rect x="{left + i * bar + 1:.1f}" y="{y:.1f}" width="{bar - 2:.1f}" height="{h:.1f}" '
                f'fill="{PALETTE[k % len(PALETTE)]}"><title>{name}: {counts[i]}</title></rect>'
            )
        if i % 2 == 0:
            shapes.append(f'<text x="{left + i * bar:.1f}" y="{height - 14}" class="a">{edges[i]:g}</text>')
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


if __name__ == "__main__":
    main(DpHistogram())
