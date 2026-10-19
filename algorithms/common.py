"""Lo que comparten los tres algoritmos: dónde deja el nodo las entradas y los parámetros, y
dónde espera las salidas (ocean-node: /data/inputs, /data/outputs)."""

import json
import os
from pathlib import Path

INPUTS = Path(os.environ.get("NODUM_INPUTS", "/data/inputs"))
OUTPUTS = Path(os.environ.get("NODUM_OUTPUTS", "/data/outputs"))
CUSTOM_DATA = "algoCustomData.json"


def input_files() -> list[Path]:
    """Los ficheros de los datasets, en orden. El nodo deja los parámetros en la misma carpeta."""
    return sorted(p for p in INPUTS.rglob("*") if p.is_file() and p.name != CUSTOM_DATA)


def parameters() -> dict[str, object]:
    """Los parámetros de consumo. El nodo los escribe siempre (vacío si no hay)."""
    path = INPUTS / CUSTOM_DATA
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def number(params: dict[str, object], name: str, default: float) -> float:
    try:
        return float(params.get(name, default))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def flag(params: dict[str, object], name: str, default: bool) -> bool:
    value = params.get(name, default)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "sí", "si", "yes"}
    return bool(value)


def write_json(name: str, data: object) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_text(name: str, text: str) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / name
    path.write_text(text, encoding="utf-8")
    return path
