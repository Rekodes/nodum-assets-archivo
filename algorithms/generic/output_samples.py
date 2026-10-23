"""Muestra de salidas: escribe un fichero de cada tipo que Nodum sabe enseñar en la ficha de una
ejecución, y los casos límite, para ver cómo se pinta cada uno.

Se publica como «Un script» (Python 3.11, solo la biblioteca estándar). No lee los datos: el dataset solo
hace falta para lanzarlo. Salidas en /data/outputs, o en OCEAN_OUTPUTS para probar en local:

    OCEAN_OUTPUTS=/tmp/out python3 algorithms/generic/output_samples.py
"""

from __future__ import annotations

import base64
import csv
import io
import json
import math
import os
import random
import struct
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(os.environ.get("OCEAN_OUTPUTS", "/data/outputs"))
INPUTS = Path(os.environ.get("OCEAN_INPUTS", "/data/inputs"))
rng = random.Random(7)

# Una foto pequeña (200 × 110, JPEG): la biblioteca estándar no sabe escribir JPEG.
PHOTO_JPEG = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEEx"
    "NDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7"
    "Ozs7Ozs7Ozs7Ozs7Ozv/wAARCABuAMgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAA"
    "AgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6"
    "Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREA"
    "AgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5"
    "OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
    "xcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwC3ijFP20ba+iueHYZijFP20baLhYZijFP2"
    "0baLhYZijFP20baLhYZijFP20baLhYZijFP20baLhYZijFP20baLhYZijFP20baLhYZijFP20baLhYZijFP20baLhYZijFP2"
    "0baLhYZijFP20baLhYZiin7aKLhYk20bafijFRcoZto20/FGKLgM20bafijFFwGbaNtPxRii4DNtG2n4oxRcBm2jbT8UYouA"
    "zbRtp+KMUXAZto20/FGKLgM20bafijFFwGbau2OlTXi78iOPONxGc/QVBDF5syR5xvYLn0ya6tEWNFRRhVAAHtXh5vmU8JFQ"
    "pfE+vZHfgsMqzblsjN/sC0/56TfmP8Ko32jSWytLE3mRjk8fMB/Wuior5uhnOLpTUnLmXZnqVMFRlGyVjjNtG2rd9brb3kkS"
    "/dByPYHnFV8V95TqqpBTjs1f7z56UXGTi+gzbRT8UVpckkxRin7aNtZ3KGYoxT9tG2i4DMUYp+2jbRcBmKMU/bRtouAzFGKf"
    "to20XAZijFP20baLgMxRin7aNtFwGYoxT9tG2i4DMUYp+2jbRcAgYRXEcjA4RgTj2NdQCGAZSCDyCO9cvtrQs9SaBBFKC6Do"
    "R1A9PevBznA1MTGM6WrXTyPQwWIjSbjLZmzRVX+0rT/nt/46f8KqXeq7lMduCM8bz1/CvmqOW4qrPl5GvNqx6k8VSgr81/Qo"
    "X8izX0rpypOAfXAxVfFP20ba+/pQVKnGC2SS+4+dnJyk5PqMxRT9tFaXJJNtG2sQ+LtOH/LK5/75X/4qm/8ACY6d/wA8bn/v"
    "lf8A4qoswujd20bawv8AhMdO/wCeF1/3yv8A8VTh4v08/wDLC5/75X/4qizC6NvbRtrGHiywP/LG5/75X/4ql/4Sqw/543H/"
    "AHyv+NOzFzx7mxto21jHxXp4/wCWVx/3yv8AjTT4u04f8srn/vlf/iqVmHNE29tG2sP/AITHTv8Anjc/98r/APFUn/CY6d/z"
    "wuv++F/+Ko1HdG7to21iDxfp5/5YXP8A3yv/AMVTh4ssD/yxuf8Avlf/AIqizDmibO2jbWP/AMJVYf8APG4/75X/ABpD4rsB"
    "/wAsrj/vlf8AGnZi549zZ20baxD4u04f8srn/vlf/iqQ+MdOH/LG5/75X/4qlZjujc20bawv+Ex07/njdf8AfK//ABVOHi/T"
    "z/ywuf8Avlf/AIqizC6NvbRtrFHiywP/ACxuf++V/wDiqd/wlVh/zxuP++V/xp2YuePc2NtG2sY+K7Af8srj/vlf8aafF2nD"
    "/llcf98r/jSsw5om3to21hnxjpw/5Y3P/fK//FUn/CY6d/zxuv8Avlf/AIqjUd0bu2isMeL9PP8Aywuf++V/+Koosw5kcXya"
    "cIyalWPFPwBWtjBz7Eax1IFApC4FMaWmTqyQsBTGkqIuTTcE0rlKHcc0hNN5NPWPNSLHQO6REEJqRY6kAAoLAU7EOTYBQKCQ"
    "KjaSoy5NFwUWyVpKjaTNM5NPWMmkXZIZkmnBCalWOnhQKLCc+xGsdSBQKCwFRtJTJ1ZJkCmNJiojITTeTSuUodx7SZpmSacI"
    "yalWOgd0iEITUix1KFAoLAU7EuTewgQCimtJRRcXK2OLgVG0lREk0oQmlctRSAsTQFJqRY6kCAUWBySIljqQRgU7gU0yAUyL"
    "tjuBSFwKiaSmFiaLjUO5I0lRlyaApNSLFSK0REATUix1KEApeBTsS59hqx4p2AKaXAqNpKBWbJS4FRtLUZYmgKTSuWopAXJp"
    "ACakWOpQgFFgckiFY6lWPFO4FIXApkXbFAApC4FRNJTCxNFxqHclaSoi5NAUmnrHSK0RHgmirAjAoosLnGrHUgUCgnFMZzTJ"
    "1Y8kCmNJURcmm8mlcpQHtJmmZJpypmpFjFA7pEYQmpFjqQKBQTinYhybAKBRkCmM5qJnNFwUWyVpMVG0maZkmnBM0rlqKQ3J"
    "NKEJqVYxUgUCiwnKxEsdSBAKUnFMZ6ZN2x+QKa0mKhZzTck0rlKA9pKYSTShc1KsYoK0REEJqRYqlCgUpOKdiHMaEApcgUxn"
    "qNnNFxKLZK0gFFV8k0Url8iP/9k="
)


def write(name: str, data: str | bytes) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)
    print(f"{name}: {path.stat().st_size} bytes")


def png(width: int, height: int, pixel) -> bytes:
    """Un PNG RGB sin comprimir de más: `pixel(x, y)` da (r, g, b)."""
    rows = b"".join(b"\x00" + bytes(c for x in range(width) for c in pixel(x, y)) for y in range(height))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def heat_color(v: float) -> tuple[int, int, int]:
    """De azul oscuro a lima, como el mapa de calor de Nodum."""
    a, b = (20, 30, 60), (216, 242, 85)
    return tuple(int(a[i] + (b[i] - a[i]) * v) for i in range(3))


def readings(n: int):
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    for i in range(n):
        t = 14 + 6 * math.sin(i / 24 * 2 * math.pi) + rng.uniform(-1, 1)
        yield {
            "timestamp": (start + timedelta(hours=i)).isoformat(),
            "sensor": f"S-{i % 3 + 1}",
            "temp_c": round(t, 2),
            "oxygen_mg_l": round(8 - 0.18 * t + rng.uniform(-0.4, 0.4), 2),
            "alert": t > 19,
        }


def images() -> None:
    # SVG: barras con su texto.
    values = [("Lun", 12), ("Mar", 19), ("Mié", 7), ("Jue", 23), ("Vie", 15), ("Sáb", 4), ("Dom", 9)]
    top = max(v for _, v in values)
    bars = "".join(
        f'<rect x="{40 + i * 52}" y="{200 - v / top * 160:.0f}" width="34" height="{v / top * 160:.0f}" rx="5" fill="#8fa3ff"/>'
        f'<text x="{57 + i * 52}" y="222" text-anchor="middle">{d}</text>'
        f'<text x="{57 + i * 52}" y="{192 - v / top * 160:.0f}" text-anchor="middle" font-weight="700">{v}</text>'
        for i, (d, v) in enumerate(values)
    )
    write(
        "imagenes/barras.svg",
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="240" viewBox="0 0 420 240" font-family="sans-serif" font-size="12" fill="#5b5f69">'
        f'<rect width="420" height="240" fill="#ffffff"/><line x1="30" y1="200" x2="410" y2="200" stroke="#d3d6db"/>{bars}</svg>',
    )
    # PNG: un mapa de calor de 7 días por 24 horas.
    cells = [[(math.sin(h / 24 * 2 * math.pi - 1.6) + 1) / 2 * (0.6 + 0.4 * rng.random()) for h in range(24)] for _ in range(7)]
    write("imagenes/mapa-de-calor.png", png(24 * 16, 7 * 16, lambda x, y: heat_color(cells[y // 16][x // 16])))
    write("imagenes/foto.jpg", base64.b64decode("".join(PHOTO_JPEG)))


def tables() -> None:
    rows = list(readings(48))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    write("tablas/lecturas.csv", buffer.getvalue())
    lines = ["sensor\tlecturas\ttemp_media_c\talertas"]
    for s in ("S-1", "S-2", "S-3"):
        mine = [r for r in rows if r["sensor"] == s]
        lines.append(f"{s}\t{len(mine)}\t{sum(r['temp_c'] for r in mine) / len(mine):.2f}\t{sum(r['alert'] for r in mine)}")
    write("tablas/resumen.tsv", "\n".join(lines) + "\n")
    # Más de 200 filas: la ficha pinta las primeras y el resto, al descargar.
    big = io.StringIO()
    writer = csv.DictWriter(big, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(readings(500))
    write("tablas/larga-500-filas.csv", big.getvalue())
    # Comas y comillas dentro de un campo.
    write("tablas/con-comillas.csv", 'nombre,nota\n"García, Ana","dijo ""hola"""\nLuis,sin comas\n')


def data() -> None:
    write(
        "datos/metricas.json",
        json.dumps(
            {"model": "logistic_regression", "metrics": {"accuracy": 0.912, "precision": 0.874, "recall": 0.861, "f1": 0.867},
             "confusion_matrix": [[412, 31], [37, 230]], "features": ["temp_c", "oxygen_mg_l", "hour"],
             "trained_at": "2026-10-21T10:00:00Z", "rows": 710, "notes": None},
            ensure_ascii=False,
        ),
    )
    write("datos/lista.json", json.dumps(list(readings(5)), ensure_ascii=False))


def documents() -> None:
    inputs = sorted(p.name for p in INPUTS.rglob("*") if p.is_file() and p.name != "algoCustomData.json") if INPUTS.exists() else []
    write(
        "informe.md",
        "# Informe de prueba\n\n"
        "Un **Markdown** con lo que la ficha pinta: *cursiva*, `código`, listas, citas y bloques.\n\n"
        "## Entradas\n\n" + ("".join(f"- `{n}`\n" for n in inputs) or "- Ninguna\n") + "\n"
        "## Pasos\n\n1. Leer los datos.\n2. Calcular las métricas.\n3. Escribir las salidas.\n\n"
        "> El HTML que traiga un Markdown se ve como texto: <b>esto no sale en negrita</b>.\n\n"
        "```\nresultado = modelo.predict(x)\n```\n\n---\n\n"
        "Más en [la documentación](https://example.org).\n",
    )
    write(
        "informe.html",
        "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>Informe</title><style>"
        "body{font-family:sans-serif;margin:24px;color:#141619}h1{font-size:20px}table{border-collapse:collapse}"
        "td,th{border:1px solid #e6e7ea;padding:6px 10px}th{background:#f1f2f4}.ok{color:#5d7205;font-weight:700}"
        "</style></head><body><h1>Informe HTML</h1><p>Se pinta aislado y sin scripts. Las imágenes van dentro, en "
        "<code>data:image/png</code>.</p><table><tr><th>Métrica</th><th>Valor</th></tr><tr><td>Exactitud</td>"
        "<td class=\"ok\">91,2 %</td></tr><tr><td>F1</td><td>0,867</td></tr></table><p><img alt=\"mapa\" src=\"data:image/png;base64,"
        + base64.b64encode(png(48, 14, lambda x, y: heat_color(x / 47))).decode()
        + "\"></p></body></html>",
    )
    # Con un script: la ficha no lo enseña y dice por qué.
    write("html-con-script.html", "<!doctype html><html><body><h1>No debería verse</h1><script>alert(1)</script></body></html>")


def texts() -> None:
    write("notas.txt", "Texto plano con acentos: ñandú, camión, pingüino.\nY una segunda línea.\n")
    start = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)
    write("ejecucion.log", "".join(f"{(start + timedelta(seconds=i)).isoformat()} INFO paso {i}: ok\n" for i in range(60)))
    # Más de 256 KiB: solo se descarga.
    write("texto-grande.txt", "".join(f"línea {i:06d} " + "x" * 60 + "\n" for i in range(4500)))


def others() -> None:
    # Sin vista: se ofrece para descargar.
    write("modelo.bin", bytes(rng.randrange(256) for _ in range(2048)))
    write("sin-extension", "Un fichero sin extensión.\n")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for step in (images, tables, data, documents, texts, others):
        step()
