"""Audita el entorno en el que el nodo ejecuta el algoritmo.

No transforma los datos: deja constancia de lo que el contenedor ve, para comprobar que el nodo
hace lo que promete (`docs/ocean/ocean-protocol.md` en ocean-hub):

- quién ejecuta (uid y gid) y con qué capacidades de Linux;
- los límites de CPU y memoria del cgroup, y el disco de /data;
- si hay red (el entorno gratuito debería no tenerla);
- las entradas con su tamaño y su sha256 (comparables con el `filesChecksum` publicado);
- los parámetros recibidos y las carpetas de /data;
- las variables de entorno, solo sus nombres (los valores pueden ser secretos).

Parámetros: `probe_host` (text, por defecto `1.1.1.1`): a qué dirección intenta conectar.
Salida: /data/outputs/env-audit.json
"""

import hashlib
import os
import platform
import shutil
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import INPUTS, OUTPUTS, input_files, parameters, write_json  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def cgroup_limits() -> dict[str, object]:
    cpu_max = read("/sys/fs/cgroup/cpu.max")  # cgroup v2: "<cuota> <periodo>" o "max <periodo>"
    cpus = None
    if cpu_max and not cpu_max.startswith("max"):
        quota, period = (int(x) for x in cpu_max.split())
        cpus = round(quota / period, 2)
    memory = read("/sys/fs/cgroup/memory.max") or read("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    return {
        "cpus": cpus,
        "visible_cpus": os.cpu_count(),
        "memory_bytes": None if memory in (None, "max") else int(memory),  # type: ignore[arg-type]
    }


def capabilities() -> dict[str, str | None]:
    status = read("/proc/self/status") or ""
    caps = {}
    for line in status.splitlines():
        if line.startswith(("CapEff", "CapPrm", "CapBnd")):
            key, value = line.split(":", 1)
            caps[key] = value.strip()
    return caps


def network(host: str) -> dict[str, object]:
    started = time.monotonic()
    try:
        with socket.create_connection((host, 443), timeout=3):
            reachable, error = True, None
    except OSError as exc:
        reachable, error = False, type(exc).__name__
    try:
        socket.getaddrinfo("example.com", 443)
        dns = True
    except OSError:
        dns = False
    return {"probe": f"{host}:443", "reachable": reachable, "error": error, "dns": dns,
            "seconds": round(time.monotonic() - started, 2)}


def tree(root: Path, depth: int = 2) -> list[str]:
    if not root.exists():
        return []
    out = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if len(rel.parts) <= depth:
            out.append(f"{rel}{'/' if path.is_dir() else ''}")
    return out


def main() -> int:
    host = str(parameters().get("probe_host") or "1.1.1.1")
    data_root = INPUTS.parent
    disk = shutil.disk_usage(data_root if data_root.exists() else Path("/"))
    report = {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "kernel": platform.release(),
        "uid": os.getuid(),
        "gid": os.getgid(),
        "capabilities": capabilities(),
        "limits": cgroup_limits(),
        "disk_free_bytes": disk.free,
        "network": network(host),
        "inputs": [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)} for p in input_files()],
        "parameters": parameters(),
        "data_tree": tree(data_root),
        "outputs_writable": os.access(OUTPUTS, os.W_OK) or not OUTPUTS.exists(),
        "environment_names": sorted(os.environ),
    }
    write_json("env-audit.json", report)
    net = report["network"]
    print(f"uid:gid {report['uid']}:{report['gid']} · CPU {report['limits']['cpus']} · "  # type: ignore[index]
          f"memoria {report['limits']['memory_bytes']} bytes")  # type: ignore[index]
    print(f"Red: {'SÍ hay salida' if net['reachable'] else 'sin salida'} ({net['probe']}), DNS {net['dns']}")  # type: ignore[index]
    for item in report["inputs"]:  # type: ignore[attr-defined]
        print(f"{item['file']}: {item['bytes']} bytes, sha256 {item['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
