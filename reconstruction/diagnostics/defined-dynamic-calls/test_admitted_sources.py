"""The sources that run are the bytes that passed the digest admission."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate  # noqa: E402


class AdmittedSourceTests(unittest.TestCase):
    def test_source_replaced_after_admission_does_not_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reviewed, marker = {}, root / 'unadmitted-ran'
            for index, name in enumerate(generate.REVIEWED):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                raw = f'VALUE = {index}\n'.encode()
                path.write_bytes(raw)
                reviewed[name] = hashlib.sha256(raw).hexdigest()
            real_read, swapped = Path.read_bytes, []

            def read_bytes(path):
                raw = real_read(path)
                if len(swapped) == len(reviewed):
                    return f'open({str(marker)!r}, "w").close()\n'.encode()
                swapped.append(path)
                return raw

            with mock.patch.dict(generate.REVIEWED, reviewed, clear=True), \
                    mock.patch.object(Path, 'read_bytes', read_bytes), \
                    mock.patch.object(generate.sys, 'path', list(generate.sys.path)):
                modules = generate.load_sources(root)
            self.assertFalse(marker.exists(), 'unadmitted bytes were executed')
            self.assertEqual([module.VALUE for module in modules[:3]], [0, 1, 2])


if __name__ == '__main__':
    unittest.main()
