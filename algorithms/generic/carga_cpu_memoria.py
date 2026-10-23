"""Carga de CPU y memoria: trabaja un rato a toda CPU y va ocupando memoria poco a poco, para ver
las métricas del nodo (una foto cada 10 s) y la serie de Nodum.

Se publica como «Un script» (Python 3.11, solo la biblioteca estándar). No lee los datos: el dataset
solo hace falta para lanzarlo. Parámetros en /data/inputs/algoCustomData.json; salidas en
/data/outputs, o en OCEAN_INPUTS y OCEAN_OUTPUTS para probar en local:

    OCEAN_OUTPUTS=/tmp/out python3 algorithms/generic/carga_cpu_memoria.py

- `segundos` (60): cuánto trabaja. El entorno gratuito corta a los 120 s, bajada de la imagen incluida.
- `memoria_mb` (400): la memoria que alcanza al final, subiendo en escalones de un segundo.
- `sin_memoria` (no): pide memoria sin parar hasta que el nodo lo mata por pasar del límite.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

INPUTS = Path(os.environ.get("OCEAN_INPUTS", "/data/inputs"))
OUTPUTS = Path(os.environ.get("OCEAN_OUTPUTS", "/data/outputs"))
MB = 1024 * 1024
# Sin memoria: escalones de 100 MB hasta 16 GB como mucho, por si el entorno no tuviera límite.
OOM_STEP_MB = 100
OOM_CEILING_MB = 16 * 1024


def read_parameters() -> dict:
    try:
        return json.loads((INPUTS / "algoCustomData.json").read_text())
    except (OSError, ValueError):
        return {}


def number(parameters: dict, name: str, default: float, low: float, high: float) -> float:
    try:
        value = float(parameters.get(name, default))
    except (TypeError, ValueError):
        value = default
    return min(high, max(low, value))


def yes(value: object) -> bool:
    return value in (True, "true", "True", 1, "1", "sí")


def busy(until: float) -> int:
    """CPU a tope hasta `until`: sha256 encadenados. Devuelve cuántos hizo."""
    digest, rounds = b"nodum", 0
    while time.monotonic() < until:
        for _ in range(2000):
            digest = hashlib.sha256(digest).digest()
        rounds += 2000
    return rounds


def run_out_of_memory() -> int:
    held: list[bytes] = []
    for step in range(1, OOM_CEILING_MB // OOM_STEP_MB + 1):
        # `bytes * n` escribe cada página: cuenta en la memoria del contenedor de verdad.
        held.append(b"\x01" * (OOM_STEP_MB * MB))
        print(f"Memoria pedida: {step * OOM_STEP_MB} MB", flush=True)
        time.sleep(0.5)
    print("Llegó al tope sin que el nodo lo parara: el entorno no tiene límite de memoria.", file=sys.stderr)
    return 4


def main() -> int:
    parameters = read_parameters()
    seconds = number(parameters, "segundos", 60, 5, 3600)
    target_mb = number(parameters, "memoria_mb", 400, 0, 64 * 1024)
    print(f"Parámetros: {parameters}", flush=True)
    if yes(parameters.get("sin_memoria")):
        return run_out_of_memory()

    held: list[bytes] = []
    timeline: list[dict] = []
    start = time.monotonic()
    total_rounds = 0
    second = 0
    while time.monotonic() - start < seconds:
        second += 1
        wanted_mb = int(target_mb * min(1.0, second / seconds))
        grow_mb = wanted_mb - len(held)
        if grow_mb > 0:
            held.extend(b"\x01" * MB for _ in range(grow_mb))
        rounds = busy(min(start + seconds, time.monotonic() + 1))
        total_rounds += rounds
        timeline.append({"segundo": second, "memoria_mb": len(held), "sha256_por_segundo": rounds})
        if second % 5 == 0:
            print(f"{second:>4} s · {len(held)} MB · {rounds} sha256/s", flush=True)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    summary = {
        "segundos": round(time.monotonic() - start, 1),
        "memoria_final_mb": len(held),
        "sha256_total": total_rounds,
        "sha256_por_segundo_medio": round(total_rounds / max(1, second)),
    }
    (OUTPUTS / "carga.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    with (OUTPUTS / "carga.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["segundo", "memoria_mb", "sha256_por_segundo"])
        writer.writeheader()
        writer.writerows(timeline)
    print(f"Hecho: {summary}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
