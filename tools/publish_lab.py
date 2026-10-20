"""Publica en Nodum lo que describe catalog/lab.json, con una clave de API.

    NODUM_API_KEY=ak_… python3 tools/publish_lab.py            # publica y confía
    NODUM_API_KEY=ak_… python3 tools/publish_lab.py --dry-run  # solo dice qué haría
    NODUM_API_KEY=ak_… python3 tools/publish_lab.py --run      # además lanza las ejecuciones de prueba

1. Comprueba la cartera.
2. Publica cada dataset en su nodo y cada algoritmo (tipo `image`, digest resuelto por Nodum) en
   los tres nodos, esperando a que cada publicación termine.
3. Hace que cada dataset confíe en los algoritmos de su lista.
4. Con `--run`, lanza las ejecuciones de `executions`, una tras otra; espera a que terminen y guarda
   en runs/<fecha>-nodum/ el log y las salidas que da Nodum.

Lo publicado se apunta en catalog/published.json: si se vuelve a lanzar, no se publica dos veces.
La clave se crea en Nodum, en Cuenta → Claves de API. Publicar gasta gas de la cartera de esa
cuenta (en la cadena de pruebas, sin valor); el saldo se pide desde la web (faucet).
Solo usa la biblioteca estándar de Python; si `certifi` está instalado, usa sus certificados (el
Python de python.org en macOS no trae los del sistema): `uv run --with certifi python tools/…`.
"""

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "lab.json"
STATE = ROOT / "catalog" / "published.json"
ALGORITHM_NODES = ["nodeds1", "nodeds2", "nodeds3"]


def tls_context() -> ssl.SSLContext:
    try:
        import certifi  # noqa: PLC0415

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class Nodum:
    def __init__(self, base: str, key: str) -> None:
        self.base = base.rstrip("/")
        self.key = key

    def raw(self, path: str) -> bytes:
        request = urllib.request.Request(f"{self.base}{path}", headers={"Authorization": f"Bearer {self.key}"})
        with urllib.request.urlopen(request, timeout=300, context=tls_context()) as response:
            return response.read()

    def call(self, method: str, path: str, body: object | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120, context=tls_context()) as response:
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"{method} {path}: {exc.code} {exc.read().decode(errors='replace')[:500]}") from exc
        except urllib.error.URLError as exc:
            raise SystemExit(f"{method} {path}: no se pudo conectar ({exc.reason})") from exc

    def wait(self, path: str, label: str, timeout: int = 900) -> dict:
        started = time.monotonic()
        last = None
        while time.monotonic() - started < timeout:
            status = self.call("GET", path)
            step = f"{status.get('status')} · {status.get('phase')}"
            if step != last:
                print(f"    {label}: {step}")
                last = step
            if status.get("status") in {"done", "failed"}:
                if status["status"] == "failed":
                    raise SystemExit(f"{label}: {status.get('error_code')} {status.get('error_message')}")
                return status
            time.sleep(4)
        raise SystemExit(f"{label}: no ha terminado en {timeout} s")


def as_text(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def parameters(spec: list[dict]) -> list[dict]:
    return [{**p, "default": as_text(p.get("default"))} for p in spec]


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"datasets": {}, "algorithms": {}, "trust": []}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def run_executions(nodum: Nodum, lab: dict, state: dict) -> None:
    folder = ROOT / "runs" / f"{time.strftime('%Y-%m-%d')}-nodum"
    for i, e in enumerate(lab["executions"], 1):
        datasets = [state["datasets"][k]["id"] for k in e["datasets"]]
        body = {"algorithm_id": state["algorithms"][e["algorithm"]]["id"], "dataset_ids": datasets,
                "parameters": {k: as_text(v) for k, v in e["parameters"].items()}}
        print(f"Ejecución {i}: {e['algorithm']} sobre {', '.join(e['datasets'])}")
        execution = nodum.call("POST", "/v1/executions", body)
        last = None
        while True:
            view = nodum.call("GET", f"/v1/executions/{execution['id']}")
            if view.get("state") != last:
                print(f"    {view.get('state')}")
                last = view.get("state")
            if view.get("state") in {"finished", "failed"}:
                break
            time.sleep(5)
        out = folder / f"{i:02d}-{e['algorithm']}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "execution.json").write_text(json.dumps(view, ensure_ascii=False, indent=2) + "\n")
        if view["state"] == "failed":
            print(f"    falló: {view.get('failure')}")
            continue
        (out / "algorithm.log").write_bytes(nodum.raw(f"/v1/executions/{execution['id']}/logs/algorithm"))
        for output in view.get("outputs") or []:
            name = output["name"] if isinstance(output, dict) else str(output)
            target = out / "outputs" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(nodum.raw(f"/v1/executions/{execution['id']}/outputs/file?name={urllib.parse.quote(name)}"))
        print(f"    resultados en {out.relative_to(ROOT)}")
        state.setdefault("executions", []).append({"algorithm": e["algorithm"], "datasets": e["datasets"],
                                                   "execution_id": execution["id"], "state": view["state"],
                                                   "job_id": view.get("job_id"), "node": view.get("node_id")})
        save_state(state)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("NODUM_URL", "https://nodum.rekodes.com"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run", action="store_true", help="lanza también las ejecuciones de prueba")
    args = parser.parse_args()
    key = os.environ.get("NODUM_API_KEY", "")
    if not key.startswith("ak_"):
        print("Falta NODUM_API_KEY (una clave de API de Nodum, ak_…)", file=sys.stderr)
        return 2
    lab = json.loads(CATALOG.read_text())
    state = load_state()
    nodum = Nodum(args.url, key)

    wallet = nodum.call("GET", "/v1/wallet")
    print(f"Cartera {wallet.get('address')} · {int(wallet.get('balance_wei', 0)) / 1e18:.4f} ETH")

    for d in lab["datasets"]:
        if d["key"] in state["datasets"]:
            continue
        print(f"Dataset {d['name']} en {d['node']}")
        if args.dry_run:
            continue
        body = {"node_id": d["node"], "url": d["url"], "name": d["name"],
                "description": d["description"], "tags": d["tags"]}
        publication = nodum.call("POST", "/v1/datasets", body)
        done = nodum.wait(f"/v1/datasets/publications/{publication['id']}", d["key"])
        state["datasets"][d["key"]] = {"id": done["dataset_id"], "did": done.get("did"), "node": d["node"]}
        save_state(state)

    for a in lab["algorithms"]:
        if a["key"] in state["algorithms"]:
            continue
        digest = nodum.call("POST", "/v1/algorithms/digest", {"image": a["image"]})["digest"]
        print(f"Algoritmo {a['name']} · {a['image']}@{digest}")
        if args.dry_run:
            continue
        body = {"kind": "image", "image": a["image"], "digest": digest, "entrypoint": a["entrypoint"],
                "language": a.get("language"), "version": a.get("version"),
                "parameters": parameters(a["parameters"]), "name": a["name"],
                "description": a["description"], "tags": a["tags"], "node_ids": ALGORITHM_NODES}
        publication = nodum.call("POST", "/v1/algorithms", body)
        done = nodum.wait(f"/v1/algorithms/publications/{publication['id']}", a["key"])
        state["algorithms"][a["key"]] = {"id": done["algorithm_id"], "did": done.get("did"),
                                         "image": a["image"], "digest": digest}
        save_state(state)

    for a in lab["algorithms"]:
        for dataset_key in a["trusted_by"]:
            pair = f"{dataset_key}<-{a['key']}"
            if pair in state["trust"]:
                continue
            print(f"Confianza: {dataset_key} admite {a['key']}")
            if args.dry_run:
                continue
            dataset = state["datasets"][dataset_key]["id"]
            nodum.call("POST", f"/v1/datasets/{dataset}/trust", {"algorithm_id": state["algorithms"][a["key"]]["id"]})
            state["trust"].append(pair)
            save_state(state)

    if args.run and not args.dry_run:
        run_executions(nodum, lab, state)

    print("Hecho." if not args.dry_run else "Simulación: no se ha publicado nada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
