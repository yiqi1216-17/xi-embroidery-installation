import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drivers.file_driver import FileOutputDriver, create_output_driver, parse_output_line
from manifest import load_manifest, pattern_by_id
from perception.matcher import ImageRecognitionSystem
from settings import load_settings


class ManifestTests(unittest.TestCase):
    def test_load_manifest_has_13_patterns(self):
        patterns = load_manifest()
        self.assertEqual(len(patterns), 13)

    def test_sequence_frame_path(self):
        frame = load_manifest()[0].sequence_frame(3)
        self.assertTrue(str(frame).endswith("video1-3.png"))


class FileDriverTests(unittest.TestCase):
    def test_emit_and_parse(self):
        pattern = pattern_by_id(load_manifest(), "video10")
        assert pattern is not None

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "state.txt"
            FileOutputDriver(out).emit(pattern, 2, confidence=0.08)
            parsed = parse_output_line(out.read_text(encoding="utf-8"))
            assert parsed is not None
            label, x, y, path = parsed
            self.assertEqual(label, "video10")
            self.assertAlmostEqual(x, -0.03)
            self.assertIn("video10-2.png", str(path))


class SettingsTests(unittest.TestCase):
    def test_modes(self):
        ex = load_settings("exhibition")
        dev = load_settings("dev")
        self.assertEqual(ex.recognition_mode, "exhibition")
        self.assertTrue(dev.perception.use_preview_assets)  # type: ignore[union-attr]

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            load_settings("accurate")

    def test_create_file_driver(self):
        self.assertEqual(
            create_output_driver(load_settings("exhibition")).__class__.__name__,
            "FileOutputDriver",
        )


class MatcherHysteresisTests(unittest.TestCase):
    def test_effective_threshold(self):
        matcher = ImageRecognitionSystem(load_settings("exhibition"))
        matcher.reference_features["video1"] = []
        self.assertEqual(matcher.effective_threshold(None), 0.05)
        self.assertEqual(matcher.effective_threshold("video1"), 0.03)


if __name__ == "__main__":
    unittest.main()
