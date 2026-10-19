"""Banco de calidad de ficheros JSON y XML.

Para cada dataset de entrada mide cuatro dimensiones, de 0 a 100:

- **Validez:** el fichero se puede leer (JSON o XML bien formado). Si no, la nota es 0 y se dice dónde
  se rompe.
- **Completitud:** qué parte de los registros tiene todos los campos esperados, y no vacíos. Los
  esperados son los que aparecen en la mayoría de los registros, más los de `required_fields`.
- **Consistencia:** qué parte de los registros tiene cada campo con el tipo de la mayoría (en XML
  todo es texto, así que mide la estructura con la completitud).
- **Unicidad:** qué parte de los registros no repite exactamente otro.

Se mide por registro, no por campo: un registro con un defecto ya no está bien. La nota final es
la media de las cuatro; un fichero que no se puede leer saca 0 en todas.

Parámetros: `required_fields` (text, campos separados por comas, opcional).
Salida: /data/outputs/quality-report.json y /data/outputs/quality-report.html (con gráficas SVG).
"""

import html
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import input_files, parameters, write_json, write_text  # noqa: E402

WEIGHTS = {"validity": 0.25, "completeness": 0.25, "consistency": 0.25, "uniqueness": 0.25}
LABELS = {
    "validity": "Validez",
    "completeness": "Completitud",
    "consistency": "Consistencia",
    "uniqueness": "Unicidad",
}


def is_empty(value: object) -> bool:
    return value is None or value == "" or value == {} or value == []


def type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def flatten(record: dict[str, object], prefix: str = "") -> dict[str, object]:
    """`{"vessel": {"name": …}}` → `{"vessel.name": …}`. Un objeto vacío cuenta como el campo vacío."""
    flat: dict[str, object] = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            flat.update(flatten(value, f"{name}."))
        else:
            flat[name] = value
    return flat


def score_records(records: list[dict[str, object]], required: list[str]) -> dict[str, object]:
    flat = [flatten(r) for r in records]
    presence = Counter(key for r in flat for key in r)
    expected = sorted({k for k, n in presence.items() if n >= len(flat) / 2} | set(required))
    complete = sum(1 for r in flat if all(not is_empty(r.get(k)) for k in expected))
    completeness = complete / len(flat)

    majority: dict[str, str] = {}
    mixed_fields = []
    for key in expected:
        types = Counter(type_name(r[key]) for r in flat if key in r and r[key] is not None)
        if not types:
            continue
        majority[key] = types.most_common(1)[0][0]
        if len(types) > 1:
            mixed_fields.append({"field": key, "types": dict(types)})
    consistent = sum(
        1 for r in flat
        if all(type_name(r[k]) == t for k, t in majority.items() if k in r and r[k] is not None)
    )
    consistency = consistent / len(flat)

    canonical = Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in records)
    duplicates = sum(n - 1 for n in canonical.values() if n > 1)
    uniqueness = 1 - duplicates / len(records) if records else 1.0

    missing = {k: len(flat) - sum(1 for r in flat if not is_empty(r.get(k))) for k in expected}
    return {
        "records": len(records),
        "scores": {
            "validity": 100.0,
            "completeness": round(100 * completeness, 1),
            "consistency": round(100 * consistency, 1),
            "uniqueness": round(100 * uniqueness, 1),
        },
        "findings": {
            "missing_or_empty": {k: v for k, v in missing.items() if v},
            "mixed_types": mixed_fields,
            "duplicates": duplicates,
        },
    }


def json_records(data: object) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        return json_records(lists[0]) if lists else [data]
    return []


def xml_records(root: ET.Element) -> list[dict[str, object]]:
    """Los hijos repetidos de la raíz son los registros; sus atributos y subelementos, los campos."""
    tags = Counter(child.tag for child in root)
    if not tags:
        return []
    tag = tags.most_common(1)[0][0]
    records = []
    for element in root.iter(tag):
        record: dict[str, object] = {f"@{k}": v for k, v in element.attrib.items()}
        for child in element:
            record[child.tag] = (child.text or "").strip()
        records.append(record)
    return records


def assess(path: Path, required: list[str]) -> dict[str, object]:
    text = path.read_bytes().decode("utf-8", errors="replace")
    head = text.lstrip()[:1]
    kind = "xml" if head == "<" or path.suffix.lower() == ".xml" else "json"
    try:
        if kind == "json":
            records = json_records(json.loads(text))
        else:
            records = xml_records(ET.fromstring(text))
    except (json.JSONDecodeError, ET.ParseError) as exc:
        scores = {"validity": 0.0, "completeness": 0.0, "consistency": 0.0, "uniqueness": 0.0}
        return {"file": path.name, "format": kind, "records": 0, "scores": scores,
                "findings": {"error": str(exc)}, "score": 0.0}
    result = score_records(records, required) if records else {
        "records": 0, "scores": dict.fromkeys(WEIGHTS, 100.0), "findings": {}}
    result["score"] = round(sum(result["scores"][k] * w for k, w in WEIGHTS.items()), 1)
    return {"file": path.name, "format": kind, **result}


def colour(score: float) -> str:
    return "#2f9e44" if score >= 95 else "#f08c00" if score >= 75 else "#e03131"


def bars_svg(report: dict[str, object]) -> str:
    """Una fila por dimensión: la barra mide la nota."""
    rows = []
    for i, (key, label) in enumerate(LABELS.items()):
        value = float(report["scores"][key])  # type: ignore[index]
        y = 8 + i * 26
        rows.append(
            f'<text x="0" y="{y + 14}" class="l">{label}</text>'
            f'<rect x="120" y="{y}" width="260" height="18" rx="4" class="t"/>'
            f'<rect x="120" y="{y}" width="{2.6 * value:.1f}" height="18" rx="4" fill="{colour(value)}"/>'
            f'<text x="390" y="{y + 14}" class="v">{value:.0f}</text>'
        )
    return f'<svg viewBox="0 0 420 112" role="img">{"".join(rows)}</svg>'


def html_report(reports: list[dict[str, object]]) -> str:
    cards = []
    for r in sorted(reports, key=lambda r: -float(r["score"])):  # type: ignore[arg-type]
        findings = html.escape(json.dumps(r["findings"], ensure_ascii=False, indent=1))
        cards.append(
            f'<section><header><h2>{html.escape(str(r["file"]))}</h2>'
            f'<span class="badge" style="background:{colour(float(r["score"]))}">{r["score"]}</span></header>'  # type: ignore[arg-type]
            f'<p>{str(r["format"]).upper()} · {r["records"]} registros</p>{bars_svg(r)}'
            f"<details><summary>Hallazgos</summary><pre>{findings}</pre></details></section>"
        )
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calidad de los datos</title>
<style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#1b1b1f;--muted:#6b6b76;--track:#ececf1;--card:#f7f7fa}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111114;--fg:#ededf0;--muted:#a0a0ab;--track:#2a2a31;--card:#1a1a1f}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:960px;padding:24px 16px}}
h1{{font-size:22px;margin:0 0 4px}} p{{color:var(--muted);margin:4px 0 12px}}
.grid{{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}}
section{{background:var(--card);border-radius:12px;padding:16px}}
header{{display:flex;justify-content:space-between;align-items:center}} h2{{font-size:16px;margin:0;word-break:break-all}}
.badge{{color:#fff;border-radius:999px;padding:2px 10px;font-weight:600}}
svg{{width:100%;height:auto}} .l{{font-size:15px;fill:var(--fg)}} .v{{font-size:15px;fill:var(--muted)}} .t{{fill:var(--track)}}
pre{{font-size:12px;white-space:pre-wrap;color:var(--muted)}}
</style>
<h1>Calidad de los datos</h1><p>{len(reports)} ficheros · la nota es la media de validez, completitud, consistencia y unicidad, medidas por registro</p>
<div class="grid">{"".join(cards)}</div></html>
"""


def main() -> int:
    raw = str(parameters().get("required_fields", "") or "")
    required = [f.strip() for f in raw.split(",") if f.strip()]
    reports = [assess(p, required) for p in input_files()]
    write_json("quality-report.json", {"required_fields": required, "files": reports})
    write_text("quality-report.html", html_report(reports))
    for r in reports:
        s = r["scores"]
        print(f"{r['file']}: {r['score']} (validez {s['validity']}, completitud {s['completeness']}, "  # type: ignore[index]
              f"consistencia {s['consistency']}, unicidad {s['uniqueness']})")  # type: ignore[index]
    return 0 if reports else 1


if __name__ == "__main__":
    sys.exit(main())
