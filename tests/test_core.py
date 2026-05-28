import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from xi_embroidery.drivers.file_driver import FileOutputDriver, parse_output_line
from xi_embroidery.manifest import load_manifest, pattern_by_id


class ManifestTests(unittest.TestCase):
    def test_load_manifest_has_13_patterns(self):
        patterns = load_manifest()
        self.assertEqual(len(patterns), 13)
        self.assertEqual(patterns[0].id, "video1")

    def test_sequence_frame_path(self):
        patterns = load_manifest()
        frame = patterns[0].sequence_frame(3)
        self.assertTrue(str(frame).endswith("video1-3.png"))


class FileDriverTests(unittest.TestCase):
    def test_emit_and_parse(self):
        patterns = load_manifest()
        pattern = pattern_by_id(patterns, "video10")
        assert pattern is not None

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "state.txt"
            driver = FileOutputDriver(out)
            driver.emit(pattern, 2)
            parsed = parse_output_line(out.read_text(encoding="utf-8"))
            assert parsed is not None
            label, x, y, path = parsed
            self.assertEqual(label, "video10")
            self.assertAlmostEqual(x, -0.03)
            self.assertAlmostEqual(y, -0.14)
            self.assertIn("video10-2.png", str(path))


if __name__ == "__main__":
    unittest.main()
