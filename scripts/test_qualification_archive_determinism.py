#!/usr/bin/env python3
"""Qualification evidence archives must not embed the wall clock.

archive() wrote tar.gz with tarfile's 'w:gz', whose gzip header carries the
current time; the archives are hashed into MANIFEST.json, so identical inputs
produced different evidence bytes on every run. The qualification drivers
execute at import, so the function is loaded directly from each source via
ast.
"""
import ast
import gzip
import tarfile
import time
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
DRIVERS = ("pump_macos_v144_qualification.py", "pump_macos_frontier_qualification.py")


def load_archive_function(name):
    source = (SCRIPTS / name).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "archive")
    module = {"gzip": gzip, "tarfile": tarfile}
    exec(compile(ast.Module(body=[function], type_ignores=[]), name, "exec"), module)
    return module["archive"]


class QualificationArchiveDeterminismTests(unittest.TestCase):
    def test_repeated_archives_of_the_same_tree_are_byte_identical(self):
        import tempfile

        for name in DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "source"
                (source / "nested").mkdir(parents=True)
                (source / "a.txt").write_bytes(b"alpha")
                (source / "nested" / "b.bin").write_bytes(b"\x00beta")
                archive = load_archive_function(name)
                first = root / "first.tar.gz"
                second = root / "second.tar.gz"
                archive(first, source)
                time.sleep(1.1)
                archive(second, source)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                self.assertNotIn(int(time.time()),
                                 (first.read_bytes()[4:8], ), "gzip mtime field looks current")


if __name__ == "__main__":
    unittest.main()
