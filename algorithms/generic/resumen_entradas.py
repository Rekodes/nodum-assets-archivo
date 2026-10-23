"""Resumen de los ficheros de entrada: bytes, líneas y una muestra de cada uno.

Solo biblioteca estándar. Lee los parámetros de /data/inputs/algoCustomData.json
y deja resumen.json, resumen.csv y resumen.md en /data/outputs.
"""

import csv
import json
import pathlib
import sys

INPUTS = pathlib.Path("/data/inputs")
OUTPUTS = pathlib.Path("/data/outputs")


def read_parameters() -> dict:
    try:
        return json.loads((INPUTS / "algoCustomData.json").read_text())
    except (OSError, ValueError):
        return {}


def main() -> int:
    parameters = read_parameters()
    sample = int(float(parameters.get("muestra", 3)))
    print(f"Parámetros: {parameters}")
    if parameters.get("fallar") in (True, "true", "True", 1):
        print("Fallo pedido con el parámetro «fallar».", file=sys.stderr)
        return 3

    rows = []
    for path in sorted(INPUTS.rglob("*")):
        if not path.is_file() or path.name == "algoCustomData.json":
            continue
        data = path.read_bytes()
        lines = data.decode("utf-8", errors="replace").splitlines()
        rows.append(
            {
                "fichero": str(path.relative_to(INPUTS)),
                "bytes": len(data),
                "lineas": len(lines),
                "muestra": lines[:sample],
            }
        )
        print(f"{path.relative_to(INPUTS)}: {len(lines)} líneas, {len(data)} bytes")

    if not rows:
        print("No hay ningún fichero de entrada.", file=sys.stderr)
        return 1

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "resumen.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    with (OUTPUTS / "resumen.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["fichero", "bytes", "lineas"])
        for row in rows:
            writer.writerow([row["fichero"], row["bytes"], row["lineas"]])
    table = [f"| {r['fichero']} | {r['bytes']} | {r['lineas']} |" for r in rows]
    markdown = [
        "# Resumen de las entradas",
        "",
        "| Fichero | Bytes | Líneas |",
        "|---|---|---|",
        *table,
    ]
    (OUTPUTS / "resumen.md").write_text("\n".join(markdown) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
