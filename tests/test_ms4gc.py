import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "MS4GC.py"

spec = importlib.util.spec_from_file_location("MS4GC", MODULE_PATH)
MS4GC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MS4GC)


class TestMS4GC(unittest.TestCase):
    def test_parse_time_to_ms(self):
        self.assertAlmostEqual(MS4GC.parse_time_to_ms("1ms"), 1.0)
        self.assertAlmostEqual(MS4GC.parse_time_to_ms("10us"), 0.01)
        self.assertAlmostEqual(MS4GC.parse_time_to_ms("1s"), 1000.0)
        self.assertAlmostEqual(MS4GC.parse_time_to_ms("5"), 5.0)
        self.assertAlmostEqual(MS4GC.parse_time_to_ms("-2ms"), -2.0)

    def test_ramp_percent(self):
        self.assertAlmostEqual(MS4GC.parse_ramp_to_ms("1%", 1.0), 0.01)
        self.assertAlmostEqual(MS4GC.parse_ramp_to_ms("2%", 5.0), 0.1)

    def test_bit_signal_center_default_shape(self):
        pairs = MS4GC.generate_bit_signal_pairs(
            bitsignal="0011010",
            timebase_ms=1.0,
            interval_ms=20.0,
            rise_ms=0.01,
            fall_ms=0.01,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
            language="en",
            phase_ms=0.0,
        )
        self.assertEqual(pairs[0], (0.0, 0.0))
        self.assertIn((1.995, 0.0), pairs)
        self.assertIn((2.005, 5.0), pairs)
        self.assertEqual(pairs[-1], (20.0, 0.0))

    def test_clock_signal_center(self):
        pairs = MS4GC.generate_clock_signal_pairs(
            low_time_ms=0.48,
            high_time_ms=0.51,
            clocks=1,
            rise_ms=0.01,
            fall_ms=0.01,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
            language="en",
            phase_ms=0.0,
        )
        expected = [
            (0.0, 0.0),
            (0.475, 0.0),
            (0.485, 5.0),
            (0.985, 5.0),
            (0.995, 0.0),
        ]
        self.assertEqual(pairs, expected)

    def test_phase_negative_interpolates_start(self):
        pairs = MS4GC.generate_bit_signal_pairs(
            bitsignal="0010100",
            timebase_ms=1.0,
            interval_ms=20.0,
            rise_ms=0.01,
            fall_ms=0.01,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
            language="en",
            phase_ms=-2.0,
        )
        self.assertEqual(pairs[0][0], 0.0)
        self.assertAlmostEqual(pairs[0][1], 2.5)
        self.assertTrue(any(abs(t - 0.005) < 1e-12 and abs(v - 5.0) < 1e-12 for t, v in pairs))
        self.assertEqual(pairs[-1], (20.0, 0.0))

    def test_negative_phase_command_line_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = MS4GC.main(["-noheader", "-timebase", "1ms", "-phase", "-2ms", "0010100"])
                self.assertEqual(exit_code, 0)
                self.assertTrue(buffer.getvalue().startswith("0.0 2.5"))
            finally:
                os.chdir(old_cwd)

    def test_save_defaults_language_and_phase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with redirect_stdout(io.StringIO()):
                    exit_code = MS4GC.main(["-language", "de", "-phase", "-0.5ms", "-save"])
                self.assertEqual(exit_code, 0)
                with open("MS4GCdefault.json", "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.assertEqual(data["language"], "de")
                self.assertAlmostEqual(data["phase_ms"], -0.5)
                self.assertEqual(data["version"], "1.06")
            finally:
                os.chdir(old_cwd)

    def test_noheader_suppresses_header(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = MS4GC.main(["-noheader", "001"])
                self.assertEqual(exit_code, 0)
                output = buffer.getvalue()
                self.assertFalse(output.startswith("MS4GC Version"))
                self.assertTrue(output.startswith("0.0 0.0"))
            finally:
                os.chdir(old_cwd)

    def test_invert_bit_signal_uses_fall_for_inverted_falling_edge(self):
        pairs = MS4GC.generate_bit_signal_pairs(
            bitsignal="01",
            timebase_ms=1.0,
            interval_ms=2.0,
            rise_ms=0.01,
            fall_ms=0.04,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
            invert=True,
            language="en",
            phase_ms=0.0,
        )
        self.assertEqual(pairs[0], (0.0, 5.0))
        self.assertIn((0.98, 5.0), pairs)
        self.assertIn((1.02, 0.0), pairs)
        self.assertEqual(pairs[-1], (2.0, 0.0))

    def test_invert_clock_preserves_time_structure_and_swaps_states(self):
        pairs = MS4GC.generate_clock_signal_pairs(
            low_time_ms=0.48,
            high_time_ms=0.51,
            clocks=1,
            rise_ms=0.02,
            fall_ms=0.04,
            edgepos="center",
            high_v=5.0,
            low_v=0.0,
            invert=True,
            language="en",
            phase_ms=0.0,
        )
        expected = [
            (0.0, 5.0),
            (0.46, 5.0),
            (0.5, 0.0),
            (0.98, 0.0),
            (1.0, 5.0),
        ]
        self.assertEqual(len(pairs), len(expected))
        for actual, wanted in zip(pairs, expected):
            self.assertAlmostEqual(actual[0], wanted[0])
            self.assertAlmostEqual(actual[1], wanted[1])

    def test_invert_can_be_saved_and_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MS4GC.main(["-invert", "-save"]), 0)
                with open("MS4GCdefault.json", "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.assertTrue(data["invert"])

                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MS4GC.main(["-noinvert", "-save"]), 0)
                with open("MS4GCdefault.json", "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self.assertFalse(data["invert"])
            finally:
                os.chdir(old_cwd)

    def test_help_and_version_are_accepted(self):
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as help_exit:
                MS4GC.main(["-help"])
        self.assertEqual(help_exit.exception.code, 0)

        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as version_exit:
                MS4GC.main(["-version"])
        self.assertEqual(version_exit.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
