"""Balance de agua diario de cada finca de maíz (FAO-56) y cuánto regar.

Con la ET0, la lluvia y el riego de cada hora, lleva día a día el agotamiento del suelo: el cultivo
gasta Kc · Ks · ET0 y la lluvia y el riego reponen. El día que el agotamiento pasa del agua fácil
(p · TAW) recomienda regar lo que falta hasta capacidad de campo, dividido entre la eficiencia del
riego. Si el dataset trae la sonda (`water_stress`), dice en cuántos días coincide con ella.

Salen totales diarios por finca, no las lecturas horarias.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

from ocean_app import Algorithm, AlgorithmError, InvalidParametersError, Job, Parameter, Record, main, read_records

log = logging.getLogger(__name__)

REQUIRED = ("timestamp", "et0_mm", "rain_mm", "irrigation_mm")
PALETTE = ("#1971c2", "#e8590c", "#2f9e44", "#ae3ec9", "#f08c00")


@dataclass
class Day:
    date: str
    et0_mm: float = 0.0
    rain_mm: float = 0.0
    irrigation_mm: float = 0.0
    probe_stress_hours: int = 0
    has_probe: bool = False


@dataclass(frozen=True)
class Soil:
    kc: float
    taw_mm: float
    p: float
    efficiency: float

    @property
    def raw_mm(self) -> float:
        return self.p * self.taw_mm


def number(row: Record, name: str) -> float:
    value = row.get(name, 0)
    return float(value) if isinstance(value, (int, float, str)) and value != "" else 0.0


def days_by_farm(rows: list[Record], default_farm: str) -> dict[str, list[Day]]:
    farms: dict[str, dict[str, Day]] = defaultdict(dict)
    for row in rows:
        farm = str(row.get("farm_id") or default_farm)
        date = str(row["timestamp"])[:10]
        day = farms[farm].setdefault(date, Day(date))
        day.et0_mm += number(row, "et0_mm")
        day.rain_mm += number(row, "rain_mm")
        day.irrigation_mm += number(row, "irrigation_mm")
        if "water_stress" in row:
            day.has_probe = True
            day.probe_stress_hours += str(row["water_stress"]).lower() in {"true", "1"}
    return {farm: [days[d] for d in sorted(days)] for farm, days in farms.items()}


def balance(days: list[Day], soil: Soil, initial_depletion: float) -> dict[str, object]:
    depletion = min(initial_depletion, soil.taw_mm)
    rows = []
    agree = with_probe = 0
    total_etc = 0.0
    for day in days:
        ks = 1.0 if depletion <= soil.raw_mm else max(0.0, (soil.taw_mm - depletion) / (soil.taw_mm - soil.raw_mm))
        etc = soil.kc * ks * day.et0_mm
        total_etc += etc
        depletion = min(soil.taw_mm, max(0.0, depletion + etc - day.rain_mm - day.irrigation_mm))
        stressed = depletion > soil.raw_mm
        rows.append({
            "date": day.date,
            "et0_mm": round(day.et0_mm, 2),
            "etc_mm": round(etc, 2),
            "rain_mm": round(day.rain_mm, 1),
            "irrigation_mm": round(day.irrigation_mm, 1),
            "depletion_mm": round(depletion, 1),
            "stress": stressed,
            "recommended_irrigation_mm": round(depletion / soil.efficiency, 1) if stressed else 0.0,
        })
        if day.has_probe:
            with_probe += 1
            # La sonda da el día por estresado si lo estuvo al menos 6 horas.
            agree += stressed == (day.probe_stress_hours >= 6)
    return {
        "days": rows,
        "summary": {
            "etc_mm": round(total_etc, 1),
            "irrigation_mm": round(sum(d.irrigation_mm for d in days), 1),
            "rain_mm": round(sum(d.rain_mm for d in days), 1),
            "stress_days": sum(1 for r in rows if r["stress"]),
            "agreement_with_probe": round(agree / with_probe, 3) if with_probe else None,
        },
    }


class IrrigationBalance(Algorithm):
    parameters = (
        Parameter("kc", "number", "Kc del cultivo", "Maíz a mitad de ciclo: 1,2 (FAO-56).", default=1.2),
        Parameter("taw_mm", "number", "Agua útil (mm)", "Agua que el suelo guarda para las raíces.", default=130),
        Parameter("p", "number", "Fracción p", "Parte del agua útil que el maíz gasta sin estrés.", default=0.55),
        Parameter("efficiency", "number", "Eficiencia del riego", "Goteo 0,9; pivote 0,85; manta 0,6.", default=0.85),
        Parameter("initial_depletion_mm", "number", "Agotamiento inicial (mm)",
                  "Lo que le falta al suelo el primer día.", default=20),
    )

    def run(self, job: Job) -> None:
        soil = Soil(job.parameters.number("kc"), job.parameters.number("taw_mm"), job.parameters.number("p"),
                    job.parameters.number("efficiency"))
        if soil.kc <= 0 or soil.taw_mm <= 0 or not 0 < soil.p < 1 or not 0 < soil.efficiency <= 1:
            raise InvalidParametersError("Parámetros no válidos: kc > 0, taw_mm > 0, 0 < p < 1 y 0 < efficiency <= 1")
        initial = job.parameters.number("initial_depletion_mm")

        farms: dict[str, dict[str, object]] = {}
        for path in job.inputs:
            rows = [r for r in read_records(path) if all(f in r for f in REQUIRED)]
            if not rows:
                log.info("%s: no tiene ET0, lluvia y riego por hora, se ignora", path.name)
                continue
            for farm, days in days_by_farm(rows, path.stem).items():
                farms[farm] = balance(days, soil, initial)
                summary: dict[str, object] = farms[farm]["summary"]  # type: ignore[assignment]
                log.info("%s: %s días de estrés de %d; coincide con la sonda en %s", farm, summary["stress_days"],
                         len(days), summary["agreement_with_probe"])
        if not farms:
            raise AlgorithmError("Ningún dataset tiene datos de riego")

        job.outputs.write_json("irrigation-balance.json", {
            "method": "Balance de agua en la zona de raíces, FAO-56 (cap. 8), paso diario",
            "soil": {"kc": soil.kc, "taw_mm": soil.taw_mm, "raw_mm": round(soil.raw_mm, 1), "p": soil.p,
                     "efficiency": soil.efficiency, "initial_depletion_mm": initial},
            "farms": farms,
        })
        job.outputs.write_text("irrigation-balance.svg", depletion_svg(farms, soil))


def depletion_svg(farms: dict[str, dict[str, object]], soil: Soil) -> str:
    """El agotamiento de cada finca día a día, con la línea del agua fácil."""
    width, height, left, top, bottom = 720, 320, 48, 40, 36
    plot_w, plot_h = width - left - 16, height - top - bottom
    first: list[dict[str, object]] = next(iter(farms.values()))["days"]  # type: ignore[assignment]
    n = max(len(first) - 1, 1)

    def y(depletion: float) -> float:
        return top + plot_h * depletion / soil.taw_mm

    lines = []
    for k, (name, data) in enumerate(farms.items()):
        days: list[dict[str, object]] = data["days"]  # type: ignore[assignment]
        points = " ".join(
            f"{left + plot_w * i / n:.1f},{y(float(d['depletion_mm'])):.1f}"  # type: ignore[arg-type]
            for i, d in enumerate(days)
        )
        colour = PALETTE[k % len(PALETTE)]
        lines.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="2"/>'
                     f'<rect x="{left + k * 150}" y="10" width="12" height="12" fill="{colour}"/>'
                     f'<text x="{left + k * 150 + 18}" y="21" class="a">{name}</text>')
    raw = y(soil.raw_mm)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Agotamiento del suelo por finca">'
        "<style>.a{font:12px system-ui,sans-serif;fill:#6b6b76}</style>"
        f'<rect width="{width}" height="{height}" fill="#fff"/>'
        f'<rect x="{left}" y="{raw:.1f}" width="{plot_w}" height="{top + plot_h - raw:.1f}" fill="#fff4e6"/>'
        f'<line x1="{left}" y1="{raw:.1f}" x2="{left + plot_w}" y2="{raw:.1f}" stroke="#f08c00" stroke-dasharray="4"/>'
        f'<text x="{left + plot_w}" y="{raw - 6:.1f}" text-anchor="end" class="a">agua fácil (p · TAW) · '
        "por debajo, estrés</text>"
        f'<text x="{left}" y="{height - 14}" class="a">{first[0]["date"]}</text>'
        f'<text x="{left + plot_w}" y="{height - 14}" text-anchor="end" class="a">{first[-1]["date"]}</text>'
        f'<text x="{left - 6}" y="{top + 4}" text-anchor="end" class="a">0</text>'
        f'<text x="{left - 6}" y="{top + plot_h}" text-anchor="end" class="a">{soil.taw_mm:g}</text>'
        f'{"".join(lines)}</svg>\n'
    )


if __name__ == "__main__":
    main(IrrigationBalance())
