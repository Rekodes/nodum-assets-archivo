"""Banco de calidad de ficheros JSON y XML.

Cuatro dimensiones de 0 a 100, medidas por registro (un registro con un defecto ya no está bien):

- Validez: el fichero se puede leer. Si no, 0 en todo y dónde se rompe.
- Completitud: registros con todos los campos esperados y no vacíos. Esperados: los de la mayoría
  de registros, más los de `required_fields`.
- Consistencia: registros con cada campo del tipo de la mayoría.
- Unicidad: registros que no repiten exactamente otro.

La nota es la media de las cuatro.
"""

from __future__ import annotations

import html
import json
import logging
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from ocean_app import Algorithm, AlgorithmError, Job, Parameter, Record, main

log = logging.getLogger(__name__)

DIMENSIONS = {"validity": "Validez", "completeness": "Completitud", "consistency": "Consistencia",
              "uniqueness": "Unicidad"}

REPORT_CSS = (
    ":root{color-scheme:light dark;--bg:#fff;--fg:#1b1b1f;--muted:#6b6b76;--track:#ececf1;--card:#f7f7fa}\n"
    "@media (prefers-color-scheme:dark){:root{--bg:#111114;--fg:#ededf0;--muted:#a0a0ab;--track:#2a2a31;"
    "--card:#1a1a1f}}\n"
    "body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:960px;"
    "padding:24px 16px}\n"
    "h1{font-size:22px;margin:0 0 4px} p{color:var(--muted);margin:4px 0 12px}\n"
    ".grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}\n"
    "section{background:var(--card);border-radius:12px;padding:16px}\n"
    "header{display:flex;justify-content:space-between;align-items:center} "
    "h2{font-size:16px;margin:0;word-break:break-all}\n"
    ".badge{color:#fff;border-radius:999px;padding:2px 10px;font-weight:600}\n"
    "svg{width:100%;height:auto} .l{font-size:15px;fill:var(--fg)} .v{font-size:15px;fill:var(--muted)} "
    ".t{fill:var(--track)}\n"
    "pre{font-size:12px;white-space:pre-wrap;color:var(--muted)}\n"
)


class UnreadableFileError(Exception):
    def __init__(self, kind: str, reason: str) -> None:
        super().__init__(reason)
        self.kind = kind


class RecordReader:
    """Los registros de un fichero JSON o XML. Lanza UnreadableFileError si no está bien formado."""

    @classmethod
    def read(cls, path: Path) -> tuple[str, list[Record]]:
        text = path.read_bytes().decode("utf-8", errors="replace")
        kind = "xml" if text.lstrip()[:1] == "<" or path.suffix.lower() == ".xml" else "json"
        try:
            if kind == "json":
                return kind, cls._from_json(json.loads(text))
            return kind, cls._from_xml(ET.fromstring(text))
        except (json.JSONDecodeError, ET.ParseError) as error:
            raise UnreadableFileError(kind, str(error)) from error

    @classmethod
    def _from_json(cls, data: object) -> list[Record]:
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            return cls._from_json(lists[0]) if lists else [data]
        return []

    @staticmethod
    def _from_xml(root: ET.Element) -> list[Record]:
        """Los hijos repetidos de la raíz son los registros; sus atributos y subelementos, los campos."""
        tags = Counter(child.tag for child in root)
        if not tags:
            return []
        tag = tags.most_common(1)[0][0]
        records = []
        for element in root.iter(tag):
            record: Record = {f"@{k}": v for k, v in element.attrib.items()}
            for child in element:
                record[child.tag] = (child.text or "").strip()
            records.append(record)
        return records


class QualityScorer:
    def __init__(self, required: list[str]) -> None:
        self._required = required

    def score(self, records: list[Record]) -> dict[str, object]:
        if not records:
            return {"records": 0, "scores": dict.fromkeys(DIMENSIONS, 100.0), "findings": {}}
        flat = [flatten(r) for r in records]
        expected = self._expected_fields(flat)
        majority, mixed = self._majority_types(flat, expected)
        complete = sum(1 for r in flat if all(not is_empty(r.get(k)) for k in expected))
        consistent = sum(
            1 for r in flat if all(type_name(r[k]) == t for k, t in majority.items() if r.get(k) is not None)
        )
        canonical = Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in records)
        duplicates = sum(n - 1 for n in canonical.values() if n > 1)
        missing = {k: sum(1 for r in flat if is_empty(r.get(k))) for k in expected}
        return {
            "records": len(records),
            "scores": {
                "validity": 100.0,
                "completeness": round(100 * complete / len(flat), 1),
                "consistency": round(100 * consistent / len(flat), 1),
                "uniqueness": round(100 * (1 - duplicates / len(records)), 1),
            },
            "findings": {
                "missing_or_empty": {k: v for k, v in missing.items() if v},
                "mixed_types": mixed,
                "duplicates": duplicates,
            },
        }

    def _expected_fields(self, flat: list[Record]) -> list[str]:
        presence = Counter(key for r in flat for key in r)
        return sorted({k for k, n in presence.items() if n >= len(flat) / 2} | set(self._required))

    @staticmethod
    def _majority_types(flat: list[Record], expected: list[str]) -> tuple[dict[str, str], list[dict[str, object]]]:
        majority: dict[str, str] = {}
        mixed: list[dict[str, object]] = []
        for key in expected:
            types = Counter(type_name(r[key]) for r in flat if r.get(key) is not None)
            if not types:
                continue
            majority[key] = types.most_common(1)[0][0]
            if len(types) > 1:
                mixed.append({"field": key, "types": dict(types)})
        return majority, mixed


class DataQuality(Algorithm):
    parameters = (
        Parameter("required_fields", "text", "Campos obligatorios",
                  "Separados por comas; se suman a los que aparecen en la mayoría de registros.", default=""),
    )

    def run(self, job: Job) -> None:
        if not job.inputs:
            raise AlgorithmError("No hay datasets de entrada")
        required = [f.strip() for f in job.parameters.text("required_fields").split(",") if f.strip()]
        scorer = QualityScorer(required)
        reports = [self._assess(path, scorer) for path in job.inputs]

        job.outputs.write_json("quality-report.json", {"required_fields": required, "files": reports})
        job.outputs.write_text("quality-report.html", html_report(reports))
        for r in reports:
            s = r["scores"]
            log.info("%s: %s (validez %s, completitud %s, consistencia %s, unicidad %s)", r["file"], r["score"],
                     s["validity"], s["completeness"], s["consistency"], s["uniqueness"])  # type: ignore[index]

    @staticmethod
    def _assess(path: Path, scorer: QualityScorer) -> dict[str, object]:
        try:
            kind, records = RecordReader.read(path)
        except UnreadableFileError as error:
            return {"file": path.name, "format": error.kind, "records": 0, "scores": dict.fromkeys(DIMENSIONS, 0.0),
                    "findings": {"error": str(error)}, "score": 0.0}
        result = scorer.score(records)
        scores: dict[str, float] = result["scores"]  # type: ignore[assignment]
        result["score"] = round(sum(scores.values()) / len(scores), 1)
        return {"file": path.name, "format": kind, **result}


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


def flatten(record: Record, prefix: str = "") -> Record:
    """`{"vessel": {"name": …}}` → `{"vessel.name": …}`. Un objeto vacío cuenta como campo vacío."""
    flat: Record = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            flat.update(flatten(value, f"{name}."))
        else:
            flat[name] = value
    return flat


def colour(score: float) -> str:
    return "#2f9e44" if score >= 95 else "#f08c00" if score >= 75 else "#e03131"


def bars_svg(scores: dict[str, float]) -> str:
    rows = []
    for i, (key, label) in enumerate(DIMENSIONS.items()):
        value = float(scores[key])
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
        score = float(r["score"])  # type: ignore[arg-type]
        findings = html.escape(json.dumps(r["findings"], ensure_ascii=False, indent=1))
        cards.append(
            f'<section><header><h2>{html.escape(str(r["file"]))}</h2>'
            f'<span class="badge" style="background:{colour(score)}">{r["score"]}</span></header>'
            f'<p>{str(r["format"]).upper()} · {r["records"]} registros</p>{bars_svg(r["scores"])}'  # type: ignore[arg-type]
            f"<details><summary>Hallazgos</summary><pre>{findings}</pre></details></section>"
        )
    return (
        '<!doctype html><html lang="es"><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Calidad de los datos</title>\n<style>\n{REPORT_CSS}</style>\n"
        "<h1>Calidad de los datos</h1>"
        f"<p>{len(reports)} ficheros · la nota es la media de validez, completitud, consistencia y unicidad, "
        "medidas por registro</p>\n"
        f'<div class="grid">{"".join(cards)}</div></html>\n'
    )


if __name__ == "__main__":
    main(DataQuality())
