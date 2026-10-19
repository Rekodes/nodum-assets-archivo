"""Boyas sintéticas con hipoxia costera, para el laboratorio de Nodum.

Tres sitios (uno por nodo: nodeds1, nodeds2, nodeds3), una medida por hora
durante 30 días. Cada sitio tiene su propio clima (datos no IID, como en un FL
real). La etiqueta `hypoxia` (oxígeno disuelto < 4 mg/L) sale de una relación
conocida con la temperatura, la clorofila y el viento, más ruido: un modelo
federado tiene algo que aprender y se sabe qué debería encontrar.

Semilla fija y JSON con claves ordenadas: los bytes salen idénticos en cada
ejecución, así el checksum que calcula el nodo no cambia. Lo publicado en `v1`
no se toca nunca (SHA256SUMS lo vigila): un cambio en los datos es un `v2`.

Uso: python3 generadores/boyas_hipoxia.py <raíz_publicada>
"""

import json
import math
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SEED = 20261019
START = datetime(2026, 7, 1, tzinfo=UTC)
HOURS = 30 * 24
HYPOXIA_THRESHOLD_MG_L = 4.0

SITES = [
    # Laguna somera y cálida: mucha clorofila, hipoxia frecuente.
    {"site_id": "site-a", "node": "nodeds1", "name": "Laguna costera",
     "lat": 37.72, "lon": -0.78, "sst_base": 27.0, "sst_amp": 1.6,
     "chl_base": 6.0, "wind_base": 4.0, "sal_base": 42.0},
    # Bahía abierta: hipoxia ocasional.
    {"site_id": "site-b", "node": "nodeds2", "name": "Bahía abierta",
     "lat": 37.58, "lon": -0.98, "sst_base": 24.5, "sst_amp": 1.1,
     "chl_base": 4.5, "wind_base": 4.5, "sal_base": 37.8},
    # Mar abierto, más fresco: hipoxia rara.
    {"site_id": "site-c", "node": "nodeds3", "name": "Mar abierto",
     "lat": 37.40, "lon": -0.55, "sst_base": 23.0, "sst_amp": 0.7,
     "chl_base": 4.5, "wind_base": 5.0, "sal_base": 37.5},
]


def oxygen_saturation_mg_l(temp_c: float, salinity_psu: float) -> float:
    """Aproximación lineal de la saturación de O2 (mg/L) en agua de mar."""
    return 14.6 - 0.39 * temp_c + 0.0072 * temp_c**2 - 0.06 * salinity_psu


def generate_site(site: dict, rng: random.Random) -> list[dict]:
    records = []
    chl = site["chl_base"]
    wind = site["wind_base"]
    for hour in range(HOURS):
        ts = START + timedelta(hours=hour)
        day_phase = 2 * math.pi * (hour % 24) / 24
        # Temperatura: ciclo diario (máximo a media tarde) y deriva lenta.
        sst = (site["sst_base"] + site["sst_amp"] * math.sin(day_phase - math.pi / 2)
               + 0.02 * hour / 24 + rng.gauss(0, 0.25))
        # Viento y clorofila: procesos autorregresivos alrededor de su base.
        wind = max(0.0, wind + 0.15 * (site["wind_base"] - wind) + rng.gauss(0, 0.8))
        chl = max(0.05, chl + 0.05 * (site["chl_base"] - chl) + rng.gauss(0, 0.25 * site["chl_base"] ** 0.5))
        salinity = site["sal_base"] + rng.gauss(0, 0.15)
        wave = max(0.05, 0.12 * wind + rng.gauss(0, 0.15))
        # Oxígeno: saturación menos el consumo por clorofila (de noche, sin
        # fotosíntesis, baja más), más la mezcla del viento.
        night = 1.0 if (hour % 24) < 6 or (hour % 24) >= 21 else 0.0
        oxygen = (oxygen_saturation_mg_l(sst, salinity)
                  - 0.42 * chl * (0.6 + 0.8 * night)
                  + 0.12 * wind + rng.gauss(0, 0.35))
        oxygen = max(0.3, oxygen)
        records.append({
            "timestamp": ts.isoformat().replace("+00:00", "Z"),
            "site_id": site["site_id"],
            "sea_surface_temp_c": round(sst, 2),
            "salinity_psu": round(salinity, 2),
            "chlorophyll_mg_m3": round(chl, 3),
            "wind_speed_m_s": round(wind, 2),
            "wave_height_m": round(wave, 2),
            "dissolved_oxygen_mg_l": round(oxygen, 2),
            "hypoxia": oxygen < HYPOXIA_THRESHOLD_MG_L,
        })
    return records


def document(sites: list[dict], records: list[dict]) -> dict:
    return {
        "name": "Boyas sintéticas: hipoxia costera",
        "version": "1.0.0",
        "synthetic": True,
        "license": "CC-BY-4.0",
        "generator": {"script": "generadores/boyas_hipoxia.py", "seed": SEED},
        "period": {"start": START.isoformat().replace("+00:00", "Z"), "hours": HOURS, "step": "PT1H"},
        "target": {"field": "hypoxia", "rule": f"dissolved_oxygen_mg_l < {HYPOXIA_THRESHOLD_MG_L}"},
        "features": ["sea_surface_temp_c", "salinity_psu", "chlorophyll_mg_m3",
                     "wind_speed_m_s", "wave_height_m"],
        "sites": [{k: s[k] for k in ("site_id", "node", "name", "lat", "lon")} for s in sites],
        "records": records,
    }


def write(path: Path, doc: dict) -> None:
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    path.write_text(text + "\n", encoding="utf-8")


def main() -> None:
    out = Path(sys.argv[1]) / "sinteticos" / "boyas-hipoxia" / "v1"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    everything = []
    for site in SITES:
        records = generate_site(site, rng)
        everything.extend(records)
        write(out / f"{site['site_id']}.json", document([site], records))
    write(out / "todas.json", document(SITES, everything))


if __name__ == "__main__":
    main()
