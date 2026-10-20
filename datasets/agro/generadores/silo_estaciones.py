"""Entradas de maíz en el silo de una cooperativa (JSON) y estaciones agroclimáticas (XML)
sintéticas, para medir la calidad de los datos en el laboratorio de Nodum y publicar agregados con
privacidad diferencial.

Las mismas 240 entradas salen en tres versiones, con defectos conocidos, para que se sepa qué tiene
que encontrar el algoritmo:

- `silo-entradas/v1/limpias.json`: sin defectos. 24 socios con un número de entregas muy distinto
  (de 2 a 42), como en una cooperativa de verdad.
- `silo-entradas/v1/sucias.json`: el 10 % sin `parcel`; el 6 % con `net_weight_kg` como texto; el
  4 % con `moisture_pct` con coma decimal («24,5»); el 5 % con `hybrid` nulo; el 4 % con `truck`
  vacío; y 20 duplicados exactos al final (el ticket que se mete dos veces).
- `silo-entradas/v1/cortadas.json`: las limpias cortadas a los 5000 bytes (JSON mal formado).
- `estaciones-agro/v1/estaciones.xml`: 120 estaciones. Al 12 % le falta el atributo `province`;
  el 8 % tiene `altitude_m` vacío; al 20 % le falta `operator`.

Semilla fija y sin fecha del sistema: los bytes salen idénticos en cada ejecución (SHA256SUMS lo
vigila). Un cambio en los datos es un `v2`.

Uso: python3 generadores/silo_estaciones.py <raíz_publicada>
"""

import json
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import quoteattr

START = datetime(2026, 10, 1, tzinfo=UTC)
DAYS = 30
RECORDS = 240
MEMBERS = 24
HYBRIDS = ["FAO 500", "FAO 600", "FAO 700"]
# Provincia y código INE de provincia, para las referencias SIGPAC.
PROVINCES = [("Zaragoza", 50), ("Huesca", 22), ("Lleida", 25), ("Valladolid", 47), ("Albacete", 2)]
OPERATORS = ["SIAR", "Comunidad de regantes", "Nodum"]
PLATE_LETTERS = "BCDFGHJKLMNPRSTVWXYZ"


def members(rng: random.Random) -> list[dict[str, object]]:
    """Socios con sus parcelas y cuánto entregan: unos pocos grandes y muchos pequeños."""
    result = []
    for i in range(MEMBERS):
        _, code = rng.choice(PROVINCES)
        municipality = rng.randrange(1, 300)
        parcels = [
            f"{code}:{municipality}:0:0:{rng.randrange(1, 40)}:{rng.randrange(1, 500)}:{rng.randrange(1, 4)}"
            for _ in range(rng.randrange(1, 5))
        ]
        result.append({"id": f"socio-{i + 1:03d}", "parcels": parcels, "weight": rng.paretovariate(1.2)})
    return result


def plate(rng: random.Random) -> str:
    return f"{rng.randrange(10000):04d} {''.join(rng.choice(PLATE_LETTERS) for _ in range(3))}"


def clean_record(i: int, partners: list[dict[str, object]], rng: random.Random) -> dict[str, object]:
    member = rng.choices(partners, weights=[float(m["weight"]) for m in partners])[0]  # type: ignore[arg-type]
    moisture = rng.uniform(17, 30)
    return {
        "ticket_id": f"tk-{i:04d}",
        "member": member["id"],
        "parcel": rng.choice(member["parcels"]),  # type: ignore[arg-type]
        "crop": "maíz",
        "hybrid": rng.choice(HYBRIDS),
        "net_weight_kg": rng.randrange(6000, 26000, 20),
        "moisture_pct": round(moisture, 1),
        # A más humedad, menos peso específico.
        "test_weight_kg_hl": round(78 - 0.35 * (moisture - 14) + rng.gauss(0, 1.2), 1),
        "impurities_pct": round(rng.uniform(0.3, 3.5), 1),
        # La báscula abre de 7:00 a 22:00 en campaña.
        "received_at": (START + timedelta(days=rng.randrange(DAYS), hours=rng.randrange(7, 22),
                                          minutes=rng.randrange(60))).strftime("%Y-%m-%dT%H:%M:00Z"),
        "truck": {"plate": plate(rng), "axles": rng.choice([3, 4, 5])},
    }


def deliveries(dirty: bool) -> str:
    rng = random.Random("silo")
    partners = members(rng)
    records = [clean_record(i, partners, rng) for i in range(RECORDS)]
    if dirty:
        defects = random.Random("silo-defectos")
        for record in records:
            roll = defects.random()
            if roll < 0.10:
                record.pop("parcel")
            elif roll < 0.16:
                record["net_weight_kg"] = str(record["net_weight_kg"])
            elif roll < 0.20:
                record["moisture_pct"] = str(record["moisture_pct"]).replace(".", ",")
            elif roll < 0.25:
                record["hybrid"] = None
            elif roll < 0.29:
                record["truck"] = {}
        records += [dict(records[i]) for i in range(0, RECORDS, 12)]
    return json.dumps(records, ensure_ascii=False, indent=1) + "\n"


def stations() -> str:
    rng = random.Random("estaciones-agro")
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', "<stations>"]
    for i in range(120):
        attrs = f' id="ag-{i:03d}"'
        if rng.random() > 0.12:
            attrs += f" province={quoteattr(rng.choice(PROVINCES)[0])}"
        altitude = "" if rng.random() < 0.08 else f"{rng.uniform(150, 1100):.0f}"
        rows.append(f"  <station{attrs}>")
        rows.append(f"    <lat>{rng.uniform(38.5, 42.5):.4f}</lat>")
        rows.append(f"    <lon>{rng.uniform(-5.5, 1.0):.4f}</lon>")
        rows.append(f"    <altitude_m>{altitude}</altitude_m>")
        rows.append(f"    <et0_mm>{rng.uniform(4.5, 8.5):.2f}</et0_mm>")
        if rng.random() > 0.2:
            rows.append(f"    <operator>{rng.choice(OPERATORS)}</operator>")
        rows.append("  </station>")
    rows.append("</stations>")
    return "\n".join(rows) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def main() -> None:
    root = Path(sys.argv[1]) / "sinteticos"
    clean = deliveries(dirty=False)
    write(root / "silo-entradas" / "v1" / "limpias.json", clean)
    write(root / "silo-entradas" / "v1" / "sucias.json", deliveries(dirty=True))
    write(root / "silo-entradas" / "v1" / "cortadas.json", clean[:5000])
    write(root / "estaciones-agro" / "v1" / "estaciones.xml", stations())


if __name__ == "__main__":
    main()
