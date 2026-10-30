"""Score inventory admission must match the saved-report overlap rule."""
import sys
from pathlib import Path
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_elf_symbols import fixture
import score


class ScoreOverlapAdmissionTests(unittest.TestCase):
    def test_overlapping_windows_are_rejected_before_a_report_is_built(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "base"
            base.mkdir()
            image = bytes(fixture())
            (base / "original.so").write_bytes(image)
            (base / "functions.tsv").write_text(
                "program\tvariant\toriginal_start\toriginal_end\n"
                "pump\tselected\t4096\t4112\n"
                "pump\tselected\t4104\t4112\n",
                encoding="utf-8",
            )
            score.BASE = base
            score._window_rows.cache_clear()
            with self.assertRaisesRegex(ValueError, "overlapping window range: 4104"):
                score.original_windows()


if __name__ == "__main__":
    unittest.main()
