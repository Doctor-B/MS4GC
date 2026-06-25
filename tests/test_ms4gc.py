import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS4GC_PATH = ROOT / "MS4GC.py"

spec = importlib.util.spec_from_file_location("MS4GC", MS4GC_PATH)
ms4gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms4gc)


class TestMS4GC(unittest.TestCase):
    def test_time_parsing(self):
        self.assertAlmostEqual(ms4gc.parse_time_to_ms("1ms"), 1.0)
        self.assertAlmostEqual(ms4gc.parse_time_to_ms("1000us"), 1.0)
        self.assertAlmostEqual(ms4gc.parse_time_to_ms("1s"), 1000.0)
        self.assertAlmostEqual(ms4gc.parse_time_to_ms("5"), 5.0)

    def test_ramp_percent(self):
        self.assertAlmostEqual(ms4gc.parse_ramp_to_ms("1%", 1.0), 0.01)
        self.assertAlmostEqual(ms4gc.parse_ramp_to_ms("5%", 2.0), 0.1)

    def test_edge_times_center(self):
        self.assertEqual(ms4gc.edge_times(1.0, 0.1, "center"), (0.95, 1.05))

    def test_bit_signal_default_center(self):
        pairs = ms4gc.generate_bit_signal_pairs(
            bitsignal="0011010",
            timebase_ms=1.0,
            interval_ms=20.0,
            rise_ms=0.01,
            fall_ms=0.01,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
        )
        self.assertEqual(pairs[0], (0.0, 0.0))
        self.assertEqual(pairs[1], (1.995, 0.0))
        self.assertEqual(pairs[2], (2.005, 5.0))
        self.assertEqual(pairs[-1], (20.0, 0.0))

    def test_clock_signal_center(self):
        pairs = ms4gc.generate_clock_signal_pairs(
            low_time_ms=0.48,
            high_time_ms=0.51,
            clocks=1,
            rise_ms=0.01,
            fall_ms=0.01,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
        )
        self.assertEqual(pairs, [
            (0.0, 0.0),
            (0.475, 0.0),
            (0.485, 5.0),
            (0.985, 5.0),
            (0.995, 0.0),
        ])

    def test_language_default_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            default_file = tmp_path / "MS4GCdefault.json"
            default_file.write_text(json.dumps({"language": "de"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(MS4GC_PATH), "-show"],
                cwd=tmp_path,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertIn("Aktuelle Defaultwerte", result.stdout)

    def test_header_is_default_and_noheader_suppresses_it(self):
        result = subprocess.run(
            [sys.executable, str(MS4GC_PATH), "001"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertTrue(result.stdout.startswith("MS4GC Version"))
        self.assertIn("command = MS4GC 001", result.stdout)

        result_noheader = subprocess.run(
            [sys.executable, str(MS4GC_PATH), "-noheader", "001"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertTrue(result_noheader.stdout.startswith("0.0 0.0"))
        self.assertNotIn("MS4GC Version", result_noheader.stdout)


if __name__ == "__main__":
    unittest.main()
