"""Lanza un trabajo de compute-to-data gratuito en un ocean-node, sin Nodum y sin la cadena, y
descarga su log y sus salidas. Sirve para reproducir las ejecuciones del laboratorio contra
cualquier nodo con entorno gratuito.

    uv run --no-project --with eth-account --with httpx python tools/free_compute.py \
      https://nodeds1.ibatec.es \
      "rekodes/nodum-line-count:0.1.0@sha256:<digest de algorithms/DIGESTS>" "python /app/main.py" \
      https://datos.rekodes.com/sinteticos/estaciones/v1/estaciones.xml \
      [--params '{"skip_header": true}'] [--env 0]

Firma con una clave de usar y tirar que crea la primera vez en `tools/lab-key.txt` (fuera de git):
la ruta gratuita no necesita saldo. Cada petición lleva un nonce mayor que el anterior de la misma
dirección; dos trabajos a la vez con la misma clave se pisan el nonce y el nodo rechaza uno.
Los datasets van por URL (`fileObject`) o, publicados, con `--dataset did:op:…:<serviceId>`.
"""

import argparse
import io
import json
import sys
import tarfile
import time
from pathlib import Path

import httpx
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils.crypto import keccak

KEY_FILE = Path(__file__).with_name("lab-key.txt")


def account() -> Account:
    if not KEY_FILE.exists():
        KEY_FILE.write_text(Account.create().key.hex())
    return Account.from_key(KEY_FILE.read_text().strip())


def sign(acct, nonce: str, command: str) -> str:
    digest = "0x" + keccak(text=f"{acct.address}{nonce}{command}").hex()
    return "0x" + acct.sign_message(encode_defunct(text=digest)).signature.hex().removeprefix("0x")


def nonce() -> str:
    time.sleep(0.002)
    return str(int(time.time() * 1000))


def demux(raw: bytes) -> str:
    out, i = bytearray(), 0
    while i + 8 <= len(raw) and raw[i] in (0, 1, 2) and raw[i + 1:i + 4] == b"\x00\x00\x00":
        size = int.from_bytes(raw[i + 4:i + 8], "big")
        out += raw[i + 8:i + 8 + size]
        i += 8 + size
    return (out if i else raw).decode("utf-8", errors="replace")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("node")
    p.add_argument("image")
    p.add_argument("entrypoint")
    p.add_argument("urls", nargs="*")
    p.add_argument("--params", default="{}")
    p.add_argument("--env", type=int, default=0)
    p.add_argument("--algo-did")
    p.add_argument("--algo-service")
    p.add_argument("--dataset", action="append", default=[], help="did:serviceId de un dataset publicado")
    p.add_argument("--out", default=str(Path(__file__).with_name("results")))
    a = p.parse_args()

    acct = account()
    node = a.node.rstrip("/")
    http = httpx.Client(timeout=60)
    envs = http.get(f"{node}/api/services/computeEnvironments").json()
    env = envs[a.env]
    print(f"cliente {acct.address} · entorno {env['id'][:18]}… · free={bool(env.get('free'))}")

    ref, digest = a.image.split("@")
    image, tag = ref.rsplit(":", 1)
    algorithm: dict = {"meta": {"container": {"image": image, "tag": tag, "entrypoint": a.entrypoint, "checksum": digest}}}
    if a.algo_did:
        algorithm.update(documentId=a.algo_did, serviceId=a.algo_service)
    params = json.loads(a.params)
    if params:
        algorithm["algocustomdata"] = params
    datasets = [{"fileObject": {"type": "url", "url": u, "method": "get"}} for u in a.urls]
    datasets += [{"documentId": d.split(":", 2)[0] + ":" + d.split(":", 2)[1], "serviceId": d.split(":", 2)[2]} for d in a.dataset]

    n = nonce()
    body = {
        "command": "freeStartCompute",
        "consumerAddress": acct.address,
        "nonce": n,
        "signature": sign(acct, n, "freeStartCompute"),
        "environment": env["id"],
        "datasets": datasets,
        "algorithm": algorithm,
        "resources": [{"id": "cpu", "amount": 1}, {"id": "ram", "amount": 1}, {"id": "disk", "amount": 1}],
        "maxJobDuration": 240,
    }
    r = http.post(f"{node}/api/services/freeCompute", json=body)
    print("freeCompute", r.status_code, r.text[:600])
    if r.status_code >= 300:
        return 1
    job_id = r.json()[0]["jobId"]
    print("jobId", job_id)

    status: dict = {}
    for _ in range(120):
        time.sleep(5)
        n = nonce()
        jobs = http.get(f"{node}/api/services/compute", params={
            "consumerAddress": acct.address, "jobId": job_id, "nonce": n,
            "signature": sign(acct, n, "getComputeStatus")}).json()
        if not jobs:
            continue
        status = jobs[0]
        print(f"  {status.get('status')} {status.get('statusText')}")
        if status.get("dateFinished") or str(status.get("statusText", "")).lower().startswith("job finished"):
            break

    out = Path(a.out) / job_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "status.json").write_text(json.dumps(status, indent=1))
    for res in status.get("results", []):
        n = nonce()
        resp = http.get(f"{node}/api/services/computeResult", params={
            "consumerAddress": acct.address, "jobId": job_id, "index": res["index"], "nonce": n,
            "signature": sign(acct, n, "getComputeResult")})
        if resp.status_code != 200:
            print(f"  {res['type']}: {resp.status_code} {resp.text[:200]}")
            continue
        raw = resp.content
        name = res.get("filename") or f"{res['type']}-{res['index']}"
        if res["type"] == "output":
            with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
                tar.extractall(out / "outputs", filter="data")
            print(f"  salida: {sorted(m.name for m in tarfile.open(fileobj=io.BytesIO(raw)).getmembers())}")
        else:
            (out / name).write_text(demux(raw))
            print(f"  {res['type']} ({name}):\n" + "\n".join("    " + l for l in demux(raw).splitlines()[-12:]))
    print("resultados en", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
