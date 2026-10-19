"""Cada algoritmo, con los datasets publicados, como lo ejecutaría el nodo: las entradas en una
carpeta, los parámetros en algoCustomData.json y las salidas en otra.

    python3 -m unittest discover -s tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "datasets" / "sinteticos"
BUOYS = [DATA / "boyas-hipoxia" / "v1" / f"site-{s}.json" for s in "abc"]
CATCHES = DATA / "capturas" / "v1"
STATIONS = DATA / "estaciones" / "v1" / "estaciones.xml"


def run(algorithm: str, inputs: list[Path], params: dict[str, object] | None = None) -> tuple[int, str, Path]:
    work = Path(tempfile.mkdtemp())
    (work / "inputs").mkdir()
    for path in inputs:
        shutil.copy(path, work / "inputs" / path.name)
    (work / "inputs" / "algoCustomData.json").write_text(json.dumps(params or {}))
    script = ROOT / "algorithms" / algorithm / f"{algorithm.replace('-', '_')}.py"
    env = {**os.environ, "NODUM_INPUTS": str(work / "inputs"), "NODUM_OUTPUTS": str(work / "outputs")}
    done = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout + done.stderr, work / "outputs"


class LineCount(unittest.TestCase):
    def test_counts_every_dataset(self) -> None:
        code, log, out = run("line-count", [STATIONS, CATCHES / "limpias.json"])
        self.assertEqual(code, 0, log)
        result = json.loads((out / "line-count.json").read_text())
        self.assertEqual(result["datasets"], 2)
        by_file = {f["file"]: f["lines"] for f in result["files"]}
        self.assertEqual(by_file["estaciones.xml"], STATIONS.read_text().count("\n"))
        self.assertEqual(result["total_lines"], sum(by_file.values()))

    def test_skip_header(self) -> None:
        _, _, out = run("line-count", [STATIONS], {"skip_header": True})
        result = json.loads((out / "line-count.json").read_text())
        self.assertEqual(result["files"][0]["lines"], STATIONS.read_text().count("\n") - 1)


class DataQuality(unittest.TestCase):
    def setUp(self) -> None:
        code, log, out = run("data-quality", [*sorted(CATCHES.glob("*.json")), STATIONS])
        self.assertEqual(code, 0, log)
        report = json.loads((out / "quality-report.json").read_text())
        self.files = {f["file"]: f for f in report["files"]}
        self.html = (out / "quality-report.html").read_text()

    def test_clean_is_perfect(self) -> None:
        self.assertEqual(self.files["limpias.json"]["score"], 100.0)

    def test_dirty_finds_the_known_defects(self) -> None:
        dirty = self.files["sucias.json"]
        self.assertLess(dirty["score"], 100.0)
        self.assertEqual(dirty["findings"]["duplicates"], 20)
        self.assertIn("port", dirty["findings"]["missing_or_empty"])
        mixed = {m["field"] for m in dirty["findings"]["mixed_types"]}
        self.assertIn("weight_kg", mixed)

    def test_truncated_is_invalid(self) -> None:
        self.assertEqual(self.files["cortadas.json"]["score"], 0.0)
        self.assertIn("error", self.files["cortadas.json"]["findings"])

    def test_xml_missing_attributes(self) -> None:
        stations = self.files["estaciones.xml"]
        self.assertEqual(stations["format"], "xml")
        self.assertIn("@region", stations["findings"]["missing_or_empty"])
        self.assertIn("<svg", self.html)


class DpHistogram(unittest.TestCase):
    def test_noisy_histogram_per_buoy(self) -> None:
        params = {"column": "sea_surface_temp_c", "epsilon": 1, "bins": 10, "lower": 18, "upper": 32}
        code, log, out = run("dp-histogram", BUOYS, params)
        self.assertEqual(code, 0, log)
        result = json.loads((out / "dp-histogram.json").read_text())
        self.assertEqual(set(result["datasets"]), {"site-a", "site-b", "site-c"})
        total = sum(result["combined_counts"])
        self.assertAlmostEqual(total, 3 * 720, delta=150)  # 30 intervalos con ruido de escala 1
        self.assertTrue((out / "dp-histogram.svg").read_text().startswith("<svg"))

    def test_rejects_bad_parameters(self) -> None:
        code, _, _ = run("dp-histogram", BUOYS, {"epsilon": 0})
        self.assertEqual(code, 2)


class HypoxiaModel(unittest.TestCase):
    def test_learns_something(self) -> None:
        code, log, out = run("hypoxia-model", BUOYS[:1], {"epochs": 150})
        self.assertEqual(code, 0, log)
        metrics = json.loads((out / "metrics.json").read_text())
        self.assertGreater(metrics["test"]["auc"], 0.75)
        model = json.loads((out / "model.json").read_text())
        self.assertEqual(len(model["weights"]), len(model["features"]))


class EnvAudit(unittest.TestCase):
    def test_reports_inputs_with_their_hash(self) -> None:
        code, log, out = run("env-audit", [STATIONS], {"probe_host": "127.0.0.1"})
        self.assertEqual(code, 0, log)
        report = json.loads((out / "env-audit.json").read_text())
        self.assertEqual(report["inputs"][0]["file"], "estaciones.xml")
        self.assertEqual(len(report["inputs"][0]["sha256"]), 64)
        self.assertIn("reachable", report["network"])


if __name__ == "__main__":
    unittest.main()
