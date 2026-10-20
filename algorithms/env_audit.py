"""Audita el entorno en el que el nodo ejecuta el algoritmo. No toca los datos.

Deja constancia de quién ejecuta y con qué capacidades, los límites de CPU y memoria, si hay red,
las entradas con su sha256, los parámetros, las carpetas de /data y los nombres (no los valores) de
las variables de entorno.
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import shutil
import socket
import time
from pathlib import Path

from ocean_app import Algorithm, Job, Parameter, main

log = logging.getLogger(__name__)


class ContainerProbe:
    """Lo que el contenedor puede ver de sí mismo."""

    @staticmethod
    def limits() -> dict[str, object]:
        cpu_max = _read("/sys/fs/cgroup/cpu.max")  # cgroup v2: "<cuota> <periodo>" o "max <periodo>"
        cpus = None
        if cpu_max and not cpu_max.startswith("max"):
            quota, period = (int(x) for x in cpu_max.split())
            cpus = round(quota / period, 2)
        memory = _read("/sys/fs/cgroup/memory.max") or _read("/sys/fs/cgroup/memory/memory.limit_in_bytes")
        return {
            "cpus": cpus,
            "visible_cpus": os.cpu_count(),
            "memory_bytes": None if memory in (None, "max") else int(memory),
        }

    @staticmethod
    def capabilities() -> dict[str, str]:
        caps = {}
        for line in (_read("/proc/self/status") or "").splitlines():
            if line.startswith(("CapEff", "CapPrm", "CapBnd")):
                key, value = line.split(":", 1)
                caps[key] = value.strip()
        return caps

    @staticmethod
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

    @staticmethod
    def tree(root: Path, depth: int = 2) -> list[str]:
        if not root.exists():
            return []
        return [
            f"{path.relative_to(root)}{'/' if path.is_dir() else ''}"
            for path in sorted(root.rglob("*"))
            if len(path.relative_to(root).parts) <= depth
        ]


class EnvAudit(Algorithm):
    parameters = (
        Parameter("probe_host", "text", "Dirección de prueba de red",
                  "A qué dirección intenta conectar para comprobar que no hay red.", default="1.1.1.1"),
    )

    def __init__(self, probe: ContainerProbe | None = None) -> None:
        self._probe = probe or ContainerProbe()

    def run(self, job: Job) -> None:
        root = job.data_root
        limits = self._probe.limits()
        network = self._probe.network(job.parameters.text("probe_host"))
        inputs = [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)} for p in job.inputs]
        job.outputs.write_json("env-audit.json", {
            "python": platform.python_version(),
            "machine": platform.machine(),
            "kernel": platform.release(),
            "uid": os.getuid(),
            "gid": os.getgid(),
            "capabilities": self._probe.capabilities(),
            "limits": limits,
            "disk_free_bytes": shutil.disk_usage(root if root.exists() else Path("/")).free,
            "network": network,
            "inputs": inputs,
            "parameters": job.parameters.received,
            "data_tree": self._probe.tree(root),
            "outputs_writable": os.access(job.outputs.directory, os.W_OK) or not job.outputs.directory.exists(),
            "environment_names": sorted(os.environ),
        })

        log.info("uid:gid %d:%d · CPU %s · memoria %s bytes", os.getuid(), os.getgid(), limits["cpus"],
                 limits["memory_bytes"])
        log.info("Red: %s (%s), DNS %s", "SÍ hay salida" if network["reachable"] else "sin salida",
                 network["probe"], network["dns"])
        for item in inputs:
            log.info("%s: %s bytes, sha256 %s", item["file"], item["bytes"], item["sha256"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


if __name__ == "__main__":
    main(EnvAudit())
