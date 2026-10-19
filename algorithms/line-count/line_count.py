"""Cuenta las líneas y los bytes de cada dataset de entrada.

Parámetros: `skip_header` (boolean, por defecto false): no cuenta la primera línea de cada fichero.
Salida: /data/outputs/line-count.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import flag, input_files, parameters, write_json  # noqa: E402


def count(path: Path, skip_header: bool) -> dict[str, object]:
    data = path.read_bytes()
    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    if skip_header and lines:
        lines -= 1
    return {"file": path.name, "lines": lines, "bytes": len(data)}


def main() -> int:
    skip_header = flag(parameters(), "skip_header", False)
    files = [count(p, skip_header) for p in input_files()]
    result = {
        "datasets": len(files),
        "total_lines": sum(int(f["lines"]) for f in files),  # type: ignore[call-overload]
        "skip_header": skip_header,
        "files": files,
    }
    write_json("line-count.json", result)
    for f in files:
        print(f"{f['file']}: {f['lines']} líneas, {f['bytes']} bytes")
    print(f"Total: {result['total_lines']} líneas en {len(files)} datasets")
    return 0 if files else 1


if __name__ == "__main__":
    sys.exit(main())
