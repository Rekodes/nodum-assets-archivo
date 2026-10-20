"""Informe de campaña del silo con privacidad diferencial por socio.

Lo que delata a un socio no es un camión, es su cosecha entera. Por eso la privacidad es por socio,
no por entrega: de cada socio cuentan como mucho `max_deliveries` entregas (las primeras), y la
sensibilidad de cada consulta es lo que puede cambiar si un socio entero entra o sale.

Cuatro consultas, cada una con ε/4 (composición secuencial): entregas, toneladas, suma de humedad e
histograma de humedad. La media divide la suma con ruido entre la cuenta con ruido, que no gasta más
privacidad. Con pocos socios el ruido pesa mucho: es el precio de proteger a cada uno entero.

Solo salen los agregados con ruido; el log no da ninguna cifra real.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ocean_app import Algorithm, AlgorithmError, InvalidParametersError, Job, Parameter, Record, main, read_records
from privacy import LaplaceMechanism

log = logging.getLogger(__name__)

QUERIES = 4
# Recortes: una entrega nunca aporta más que esto a una suma.
WEIGHT_KG = (0.0, 30000.0)
MOISTURE_PCT = (10.0, 40.0)
MOISTURE_EDGES = (14.0, 18.0, 22.0, 26.0, 30.0, 34.0)


@dataclass(frozen=True)
class Delivery:
    member: str
    received_at: str
    net_weight_kg: float
    moisture_pct: float

    @classmethod
    def parse(cls, row: Record) -> Delivery | None:
        """Una entrega con todos sus campos numéricos, o None: lo que no se puede leer no cuenta."""
        try:
            return cls(
                member=str(row["member"]),
                received_at=str(row.get("received_at", "")),
                net_weight_kg=float(row["net_weight_kg"]),  # type: ignore[arg-type]
                moisture_pct=float(row["moisture_pct"]),  # type: ignore[arg-type]
            )
        except (KeyError, TypeError, ValueError):
            return None


def clip(value: float, bounds: tuple[float, float]) -> float:
    return min(max(value, bounds[0]), bounds[1])


def bounded(deliveries: list[Delivery], cap: int) -> list[Delivery]:
    """Las primeras `cap` entregas de cada socio."""
    by_member: dict[str, list[Delivery]] = defaultdict(list)
    for d in sorted(deliveries, key=lambda d: d.received_at):
        if len(by_member[d.member]) < cap:
            by_member[d.member].append(d)
    return [d for ds in by_member.values() for d in ds]


def moisture_bin(value: float) -> int:
    for i in range(len(MOISTURE_EDGES) - 1):
        if value < MOISTURE_EDGES[i + 1]:
            return i
    return len(MOISTURE_EDGES) - 2


class PrivateReport:
    def __init__(self, epsilon: float, cap: int, mechanism: LaplaceMechanism) -> None:
        self._epsilon = epsilon / QUERIES
        self._cap = cap
        self._mechanism = mechanism

    def _noisy(self, value: float, per_delivery: float) -> float:
        return value + self._mechanism.noise(self._cap * per_delivery, self._epsilon)

    def build(self, deliveries: list[Delivery]) -> dict[str, object]:
        kept = bounded(deliveries, self._cap)
        count = self._noisy(len(kept), 1)
        tonnes = self._noisy(sum(clip(d.net_weight_kg, WEIGHT_KG) for d in kept), WEIGHT_KG[1]) / 1000
        moisture = self._noisy(sum(clip(d.moisture_pct, MOISTURE_PCT) for d in kept), MOISTURE_PCT[1])
        counts = [0] * (len(MOISTURE_EDGES) - 1)
        for d in kept:
            counts[moisture_bin(d.moisture_pct)] += 1
        # Cada socio cambia como mucho `cap` entregas de intervalo: sensibilidad L1 = cap.
        histogram = [max(0.0, round(self._noisy(c, 1), 1)) for c in counts]
        return {
            "deliveries": round(max(0.0, count)),
            "tonnes": round(max(0.0, tonnes), 1),
            "mean_moisture_pct": round(moisture / count, 1) if count >= 1 else None,
            "moisture_histogram": histogram,
        }


class DpSiloReport(Algorithm):
    parameters = (
        Parameter("epsilon", "number", "ε (privacidad)",
                  "Para todo el informe de cada dataset. Más pequeño, más ruido.", default=5, required=True),
        Parameter("max_deliveries", "number", "Entregas por socio",
                  "Cuántas entregas de cada socio cuentan como mucho. Más, menos sesgo y más ruido.", default=5),
    )

    def run(self, job: Job) -> None:
        epsilon = job.parameters.number("epsilon")
        cap = job.parameters.integer("max_deliveries")
        if epsilon <= 0 or cap < 1:
            raise InvalidParametersError("Parámetros no válidos: epsilon > 0 y max_deliveries >= 1")

        report = PrivateReport(epsilon, cap, LaplaceMechanism())
        datasets: dict[str, dict[str, object]] = {}
        for path in job.inputs:
            deliveries = self._deliveries(path)
            if not deliveries:
                log.info("%s: no tiene entregas de silo legibles, se ignora", path.name)
                continue
            datasets[path.stem] = report.build(deliveries)
            log.info("%s: informe publicado con ε=%g y %d entregas por socio como mucho", path.name, epsilon, cap)
        if not datasets:
            raise AlgorithmError("Ningún dataset tiene entregas de silo")

        job.outputs.write_json("dp-silo-report.json", {
            "epsilon_per_dataset": epsilon,
            "max_deliveries_per_member": cap,
            "privacy_unit": "socio",
            "mechanism": f"Laplace; {QUERIES} consultas con ε/{QUERIES} cada una; recortes por entrega: "
                         f"net_weight_kg {WEIGHT_KG}, moisture_pct {MOISTURE_PCT}",
            "moisture_edges": list(MOISTURE_EDGES),
            "datasets": datasets,
        })
        job.outputs.write_text("dp-silo-report.svg", report_svg(datasets, epsilon))

    @staticmethod
    def _deliveries(path: Path) -> list[Delivery]:
        return [d for d in (Delivery.parse(r) for r in read_records(path)) if d is not None]


def report_svg(datasets: dict[str, dict[str, object]], epsilon: float) -> str:
    """Una tarjeta por dataset: cifras y el histograma de humedad."""
    width, card = 720, 200
    height = 40 + card * len(datasets)
    parts = []
    for k, (name, data) in enumerate(datasets.items()):
        top = 40 + k * card
        counts: list[float] = data["moisture_histogram"]  # type: ignore[assignment]
        peak = max(counts) or 1.0
        bar = 300 / len(counts)
        parts.append(
            f'<text x="16" y="{top + 18}" class="h">{name}</text>'
            f'<text x="16" y="{top + 48}" class="a">Entregas: {data["deliveries"]}</text>'
            f'<text x="16" y="{top + 72}" class="a">Toneladas: {data["tonnes"]}</text>'
            f'<text x="16" y="{top + 96}" class="a">Humedad media: {data["mean_moisture_pct"]} %</text>'
        )
        for i, c in enumerate(counts):
            h = 120 * c / peak
            x = 380 + i * bar
            parts.append(
                f'<rect x="{x + 2:.1f}" y="{top + 150 - h:.1f}" width="{bar - 4:.1f}" height="{h:.1f}" fill="#f08c00">'
                f"<title>{c}</title></rect>"
                f'<text x="{x:.1f}" y="{top + 168}" class="a">{MOISTURE_EDGES[i]:g}</text>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Informe del silo con ε={epsilon:g}">'
        "<style>.a{font:13px system-ui,sans-serif;fill:#3b3b45}.h{font:600 15px system-ui,sans-serif;fill:#1b1b1f}"
        "</style>"
        f'<rect width="{width}" height="{height}" fill="#fff"/>'
        f'<text x="16" y="24" class="a">Informe de campaña con privacidad por socio · ε = {epsilon:g} · '
        "histograma de humedad (%)</text>"
        f'{"".join(parts)}</svg>\n'
    )


if __name__ == "__main__":
    main(DpSiloReport())
