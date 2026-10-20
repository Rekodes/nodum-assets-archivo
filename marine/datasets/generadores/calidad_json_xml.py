"""Capturas pesqueras (JSON) y estaciones costeras (XML) sintéticas, para medir la calidad de
datos en el laboratorio de Nodum (algoritmo `nodum-data-quality`).

Los mismos 240 registros salen en tres versiones, con defectos conocidos, para que se sepa qué
tiene que encontrar el algoritmo:

- `capturas/v1/limpias.json`: sin defectos.
- `capturas/v1/sucias.json`: el 10 % sin `port`; el 6 % con `weight_kg` como texto; el 5 % con
  `species` nulo; el 4 % con `vessel` vacío; y 20 duplicados exactos al final.
- `capturas/v1/cortadas.json`: las limpias cortadas a los 5000 bytes (JSON mal formado).
- `estaciones/v1/estaciones.xml`: 120 estaciones. Al 12 % le falta el atributo `region`; el 8 %
  tiene `depth_m` vacío; al 20 % le falta `operator`.

Semilla fija y sin fecha del sistema: los bytes salen idénticos en cada ejecución (SHA256SUMS lo
vigila). Un cambio en los datos es un `v2`.

Uso: python3 generadores/calidad_json_xml.py <raíz_publicada>
"""

import json
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import quoteattr

START = datetime(2026, 9, 1, tzinfo=UTC)
HOURS = 30 * 24
RECORDS = 240
SPECIES = ["Thunnus thynnus", "Sardina pilchardus", "Engraulis encrasicolus", "Merluccius merluccius"]
PORTS = ["Vigo", "Cádiz", "Santander", "Palma", "Valencia"]


def clean_record(i: int, rng: random.Random) -> dict[str, object]:
    return {
        "id": f"cap-{i:04d}",
        "species": rng.choice(SPECIES),
        "port": rng.choice(PORTS),
        "weight_kg": round(rng.uniform(5, 900), 1),
        "landed_at": (START + timedelta(hours=rng.randrange(HOURS))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vessel": {"name": f"Nodum {rng.randrange(1, 40)}", "length_m": round(rng.uniform(8, 40), 1)},
    }


def catches(dirty: bool) -> str:
    rng = random.Random("capturas")
    records = [clean_record(i, rng) for i in range(RECORDS)]
    if dirty:
        defects = random.Random("capturas-defectos")
        for record in records:
            roll = defects.random()
            if roll < 0.10:
                record.pop("port")
            elif roll < 0.16:
                record["weight_kg"] = str(record["weight_kg"])
            elif roll < 0.21:
                record["species"] = None
            elif roll < 0.25:
                record["vessel"] = {}
        records += [dict(records[i]) for i in range(0, RECORDS, 12)]
    return json.dumps(records, ensure_ascii=False, indent=1) + "\n"


def stations() -> str:
    rng = random.Random("estaciones")
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', "<stations>"]
    for i in range(120):
        attrs = f' id="st-{i:03d}"'
        if rng.random() > 0.12:
            attrs += f" region={quoteattr(rng.choice(PORTS))}"
        depth = "" if rng.random() < 0.08 else f"{rng.uniform(5, 4000):.0f}"
        rows.append(f"  <station{attrs}>")
        rows.append(f"    <lat>{rng.uniform(35, 44):.4f}</lat>")
        rows.append(f"    <lon>{rng.uniform(-10, 4):.4f}</lon>")
        rows.append(f"    <depth_m>{depth}</depth_m>")
        if rng.random() > 0.2:
            rows.append(f"    <operator>{rng.choice(['IEO', 'Puertos', 'Nodum'])}</operator>")
        rows.append("  </station>")
    rows.append("</stations>")
    return "\n".join(rows) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def main() -> None:
    root = Path(sys.argv[1]) / "sinteticos"
    clean = catches(dirty=False)
    write(root / "capturas" / "v1" / "limpias.json", clean)
    write(root / "capturas" / "v1" / "sucias.json", catches(dirty=True))
    write(root / "capturas" / "v1" / "cortadas.json", clean[:5000])
    write(root / "estaciones" / "v1" / "estaciones.xml", stations())


if __name__ == "__main__":
    main()
